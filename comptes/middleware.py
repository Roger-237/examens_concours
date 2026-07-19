from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied


# ─────────────────────────────────────────
#  URLs accessibles sans connexion
# ─────────────────────────────────────────
URLS_PUBLIQUES = [
    '/',
    '/auth/connexion/',
    '/auth/deconnexion/',
    '/privacy-policy/',
]


class IntermediaireRole:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        chemin = request.path

        # ── Laisse passer l'admin Django et les fichiers statiques ──
        if chemin.startswith('/django-admin/') or chemin.startswith('/static/') or chemin.startswith('/media/'):
            return self.get_response(request)

        # ── URLs publiques ──
        if any(chemin.startswith(url) for url in URLS_PUBLIQUES):
            return self.get_response(request)

        # ── Non connecté → page connexion ──
        # IMPORTANT : on appelle get_response d'abord pour que SessionMiddleware
        # puisse sauvegarder la session correctement avant de rediriger.
        if not request.user.is_authenticated:
            reponse = redirect(f'/auth/connexion/?suite={chemin}')
            return reponse

        # ── Élève suspendu ──
        if request.user.role == 'eleve':
            try:
                if request.user.eleve.est_suspendu():
                    from django.contrib.auth import logout
                    logout(request)
                    from django.contrib import messages
                    messages.error(request, 'Votre compte a été suspendu.')
                    return redirect('/auth/connexion/')
            except Exception:
                pass

        # ── Cloisonnement des rôles ──
        if request.user.role == 'eleve' and chemin.startswith('/admin/'):
            return redirect('/eleve/tableau-de-bord/')

        if request.user.role == 'admin' and chemin.startswith('/eleve/'):
            return redirect('/admin/tableau-de-bord/')

        return self.get_response(request)


# ─────────────────────────────────────────
#  MIXINS PROTECTION VUES
# ─────────────────────────────────────────
class ConnexionRequise:

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/auth/connexion/?suite={request.path}')
        return super().dispatch(request, *args, **kwargs)


class AdminRequis(ConnexionRequise):

    def dispatch(self, request, *args, **kwargs):
        # 1. Vérifier la connexion (via ConnexionRequise)
        if not request.user.is_authenticated:
            return redirect(f'/auth/connexion/?suite={request.path}')
        # 2. Vérifier le rôle
        if request.user.role != 'admin':
            raise PermissionDenied
        # 3. Continuer vers la vue
        return super(ConnexionRequise, self).dispatch(request, *args, **kwargs)


class EleveRequis(ConnexionRequise):

    def dispatch(self, request, *args, **kwargs):
        # 1. Vérifier la connexion (via ConnexionRequise)
        if not request.user.is_authenticated:
            return redirect(f'/auth/connexion/?suite={request.path}')
        # 2. Vérifier le rôle
        if request.user.role != 'eleve':
            raise PermissionDenied
        # 3. Continuer vers la vue
        return super(ConnexionRequise, self).dispatch(request, *args, **kwargs)


# ─────────────────────────────────────────
#  RATE LIMITING MIDDLEWARE
# ─────────────────────────────────────────
import hashlib
from django.core.cache import cache
from django.shortcuts import render

def obtenir_ip_client(request):
    """
    Récupère l'IP réelle de l'utilisateur sur PythonAnywhere.
    Prend le premier élément de HTTP_X_FORWARDED_FOR s'il existe.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # On applique le rate limit uniquement sur les requêtes POST vers la connexion
        if request.path == '/auth/connexion/' and request.method == 'POST':
            ip = obtenir_ip_client(request)
            
            # Récupération et anonymisation de l'identifiant pour le cache
            identifiant = request.POST.get('identifiant', '').strip().lower()
            identifiant_hash = hashlib.sha256(identifiant.encode('utf-8')).hexdigest() if identifiant else 'unknown'
            
            # Clés de cache distinctes
            cle_ip = f"rl_ip_{ip}"
            cle_user = f"rl_user_{identifiant_hash}"
            
            # 1. Rate limit par IP (seuil généreux pour les réseaux partagés, ex: 30 tentatives/minute)
            tentatives_ip = cache.get(cle_ip, 0)
            if tentatives_ip >= 30:
                return render(request, '429.html', status=429)
                
            # 2. Rate limit par Utilisateur (seuil strict de 5 tentatives/minute sur un compte)
            tentatives_user = cache.get(cle_user, 0)
            if tentatives_user >= 5:
                return render(request, '429.html', status=429)
            
            # Incrémentation des compteurs dans le cache (expiration après 60 secondes)
            cache.set(cle_ip, tentatives_ip + 1, timeout=60)
            cache.set(cle_user, tentatives_user + 1, timeout=60)
            
        return self.get_response(request)