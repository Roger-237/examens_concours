from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Lire .env ─────────────────────────────────────────────────
def lire_env():
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne and not ligne.startswith('#') and '=' in ligne:
                    cle, valeur = ligne.split('=', 1)
                    os.environ.setdefault(cle.strip(), valeur.strip())

lire_env()

SECRET_KEY    = os.environ.get('SECRET_KEY', 'django-insecure-changez-moi')
DEBUG         = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# ── Applications ───────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps locales
    'comptes',
    'examens',
]

# ── Middleware ─────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Middleware custom
    'comptes.middleware.IntermediaireRole',
]

ROOT_URLCONF = 'config.urls'

# ── Templates ──────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ── Base de données ────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME'  : BASE_DIR / 'db.sqlite3',
    }
}
# ── Modèle utilisateur custom ──────────────────────────────────
AUTH_USER_MODEL = 'comptes.Utilisateur'

# ── Validation mots de passe ───────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

# ── Internationalisation ───────────────────────────────────────
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'Africa/Libreville'
USE_I18N      = True
USE_TZ        = True

# ── Fichiers statiques ─────────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

# ── Fichiers média ─────────────────────────────────────────────
MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Clé primaire par défaut ────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Redirection connexion ──────────────────────────────────────
LOGIN_URL = '/auth/connexion/'

# ── Sessions ───────────────────────────────────────────────────
SESSION_ENGINE      = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE  = 86400          # 24h
SESSION_SAVE_EVERY_REQUEST = True    # force la sauvegarde à chaque requête
SESSION_COOKIE_HTTPONLY    = True
