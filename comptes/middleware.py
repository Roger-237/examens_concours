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