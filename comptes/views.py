from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views import View
from django.core.cache import cache

from .models import Utilisateur, Eleve, Role, CodeParrainage, Parrainage, Notification
from .formulaires import FormulaireConnexion
import hashlib


# ─────────────────────────────────────────
#  UTILITAIRE — Empreinte appareil
# ─────────────────────────────────────────
def generer_empreinte(request):
    donnees = (
        request.META.get('HTTP_USER_AGENT', '') +
        request.META.get('HTTP_ACCEPT_LANGUAGE', '') +
        request.META.get('HTTP_ACCEPT_ENCODING', '')
    )
    return hashlib.sha256(donnees.encode()).hexdigest()


# ─────────────────────────────────────────
#  UTILITAIRE — Rate limiting
# ─────────────────────────────────────────
def get_client_ip(request):
    """Récupère l'adresse IP du client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def verifier_rate_limit(ip_address, max_attempts=5, window_minutes=15):
    """Vérifie si l'IP a dépassé la limite de tentatives"""
    cache_key = f'login_attempts_{ip_address}'
    attempts = cache.get(cache_key, 0)

    if attempts >= max_attempts:
        return False, f"Trop de tentatives. Réessayez dans {window_minutes} minutes."

    return True, None


def incrementer_rate_limit(ip_address, window_minutes=15):
    """Incrémente le compteur de tentatives"""
    cache_key = f'login_attempts_{ip_address}'
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, window_minutes * 60)


def reinitialiser_rate_limit(ip_address):
    """Réinitialise le compteur après connexion réussie"""
    cache_key = f'login_attempts_{ip_address}'
    cache.delete(cache_key)


# ─────────────────────────────────────────
#  UTILITAIRE — Traiter le parrainage
# ─────────────────────────────────────────
def traiter_parrainage(eleve_filleul, code_saisi):
    """Vérifie le code parrainage et enregistre le parrainage"""
    if not code_saisi:
        return

    try:
        code_obj = CodeParrainage.objects.select_related('eleve').get(code=code_saisi)
        parrain  = code_obj.eleve

        # Évite l'auto-parrainage
        if parrain == eleve_filleul:
            return

        # Évite les doublons
        if Parrainage.objects.filter(parrain=parrain, filleul=eleve_filleul).exists():
            return

        # Crée le parrainage
        Parrainage.objects.create(parrain=parrain, filleul=eleve_filleul)

        # Compte les parrainages du parrain
        total = Parrainage.objects.filter(parrain=parrain).count()

        # Notification au parrain
        Notification.objects.create(
            destinataire=parrain.utilisateur,
            type_notif='parrainage',
            message=f"{eleve_filleul.nom_complet} a rejoint ExamensPro grâce à votre code ! Vous avez {total} parrainage(s)."
        )

        # Bonus atteint → 5 parrainages
        if total == 5:
            Notification.objects.create(
                destinataire=parrain.utilisateur,
                type_notif='bonus',
                message=f"🎉 Félicitations ! Vous avez atteint 5 parrainages. Vous bénéficiez d'un bonus de 2500 FCFA (25%). L'administrateur vous contactera."
            )

            # Notification à l'admin
            admins = Utilisateur.objects.filter(role=Role.ADMIN)
            for admin in admins:
                Notification.objects.create(
                    destinataire=admin,
                    type_notif='bonus',
                    message=f"💰 L'élève {parrain.nom_complet} a atteint 5 parrainages. Bonus de 2500 FCFA à verser."
                )

    except CodeParrainage.DoesNotExist:
        pass


# ─────────────────────────────────────────
#  CONNEXION
# ─────────────────────────────────────────
class VueConnexion(View):

    def get(self, request):
        if request.user.is_authenticated:
            return self._rediriger_selon_role(request.user)
        formulaire = FormulaireConnexion()
        return render(request, 'comptes/connexion.html', {'form': formulaire})

    def post(self, request):
        formulaire = FormulaireConnexion(request.POST)
        if formulaire.is_valid():
            identifiant   = formulaire.cleaned_data['identifiant'].strip()
            code_acces    = formulaire.cleaned_data['code_acces'].strip()
            code_parrain  = formulaire.cleaned_data.get('code_parrainage', '').strip()

            # ── Protection contre force brute ──
            ip_address = get_client_ip(request)
            peut_se_connecter, message_erreur = verifier_rate_limit(ip_address)
            if not peut_se_connecter:
                messages.error(request, message_erreur)
                return render(request, 'comptes/connexion.html', {'form': formulaire})

            # ── Tentative connexion Admin ──
            try:
                utilisateur_admin = Utilisateur.objects.get(
                    username=identifiant,
                    role=Role.ADMIN
                )
                if utilisateur_admin.check_password(code_acces):
                    utilisateur_admin.backend = 'django.contrib.auth.backends.ModelBackend'
                    login(request, utilisateur_admin)
                    # Régénérer la session pour éviter session fixation
                    request.session.cycle_key()
                    reinitialiser_rate_limit(ip_address)
                    return self._rediriger_selon_role(utilisateur_admin)
                else:
                    incrementer_rate_limit(ip_address)
            except Utilisateur.DoesNotExist:
                incrementer_rate_limit(ip_address)

            # ── Tentative connexion Élève ──
            try:
                eleve = Eleve.objects.select_related('utilisateur').get(
                    nom_complet__iexact=identifiant,
                    code_acces=code_acces,
                )

                if eleve.est_suspendu():
                    messages.error(request, 'Votre compte a été suspendu. Contactez l\'administrateur.')
                    return render(request, 'comptes/connexion.html', {'form': formulaire})

                empreinte_actuelle = generer_empreinte(request)

                if eleve.empreinte_device and eleve.empreinte_device != empreinte_actuelle:
                    eleve.statut = 'suspendu'
                    eleve.save()
                    messages.error(request, 'Connexion suspecte détectée. Votre compte a été suspendu.')
                    return render(request, 'comptes/connexion.html', {'form': formulaire})

                # ── Première connexion ──
                if not eleve.empreinte_device:
                    eleve.empreinte_device = empreinte_actuelle
                    eleve.save()

                    # Traiter le parrainage uniquement à la 1ère connexion
                    if code_parrain:
                        traiter_parrainage(eleve, code_parrain)

                eleve.utilisateur.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, eleve.utilisateur)
                # Régénérer la session pour éviter session fixation
                request.session.cycle_key()
                reinitialiser_rate_limit(ip_address)
                return self._rediriger_selon_role(eleve.utilisateur)

            except Eleve.DoesNotExist:
                incrementer_rate_limit(ip_address)

            messages.error(request, 'Identifiant ou code d\'accès incorrect.')

        return render(request, 'comptes/connexion.html', {'form': formulaire})

    def _rediriger_selon_role(self, utilisateur):
        redirections = {
            Role.ADMIN : '/admin/tableau-de-bord/',
            Role.ELEVE : '/eleve/tableau-de-bord/',
        }
        return redirect(redirections.get(utilisateur.role, '/'))


# ─────────────────────────────────────────
#  DÉCONNEXION
# ─────────────────────────────────────────
class VueDeconnexion(View):

    def post(self, request):
        logout(request)
        return redirect('/')


# ─────────────────────────────────────────
#  POLITIQUE DE CONFIDENTIALITÉ
# ─────────────────────────────────────────
class VuePrivacyPolicy(View):

    def get(self, request):
        return render(request, 'privacy_policy.html')