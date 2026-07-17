# Guide de déploiement en production (PythonAnywhere)

## Étapes pour déployer les corrections de sécurité sur examen.pythonanywhere.com

### 1. Fichiers modifiés à déployer

Les fichiers suivants ont été modifiés pour corriger les failles de sécurité :

- `comptes/views.py` : Rate limiting + régénération de session
- `comptes/middleware.py` : Validation du Referer
- `config/settings.py` : Variables d'environnement pour SECRET_KEY, DEBUG, ALLOWED_HOSTS
- `requirements.txt` : Ajout de python-dotenv
- `.env` : Fichier de configuration local (NE PAS DÉPLOYER)
- `.env.example` : Template pour la configuration production

### 2. Configuration sur PythonAnywhere

#### 2.1. Créer le fichier .env sur PythonAnywhere

Dans le dashboard PythonAnywhere :
- Allez dans "Files"
- Naviguez vers votre dossier de projet
- Créez un fichier `.env` avec le contenu suivant :

```bash
SECRET_KEY=generer_une_cle_secrete_aleatoire_ici
DEBUG=False
ALLOWED_HOSTS=examen.pythonanywhere.com
```

**Générer une SECRET_KEY sécurisée :**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### 2.2. Mettre à jour requirements.txt

Sur PythonAnywhere, dans le dashboard :
- Allez dans "Web" → votre application
- Cliquez sur "Code" → "requirements.txt"
- Ajoutez cette ligne :
```
python-dotenv==1.0.0
```
- Cliquez sur "Reload" pour installer

#### 2.3. Déployer les fichiers modifiés

Utilisez Git pour déployer :

```bash
# Sur votre machine locale
git add comptes/views.py comptes/middleware.py config/settings.py requirements.txt .env.example
git commit -m "Correction failles sécurité : rate limiting, session fixation, referer validation"
git push
```

Sur PythonAnywhere :
- Allez dans "Consoles" → "Bash"
- Naviguez vers votre dossier de projet
- Exécutez :
```bash
git pull
```

#### 2.4. Redémarrer l'application

Dans le dashboard PythonAnywhere :
- Allez dans "Web" → votre application
- Cliquez sur le bouton "Reload"

### 3. Vérification après déploiement

#### 3.1. Vérifier que l'application fonctionne

Visitez : https://examen.pythonanywhere.com/

#### 3.2. Tester la connexion admin

- Essayez de vous connecter avec votre compte admin
- Vérifiez que la connexion fonctionne

#### 3.3. Tester le rate limiting

Essayez de vous connecter avec un mauvais mot de passe 6 fois de suite. La 6ème tentative devrait être bloquée.

#### 3.4. Tester la validation du Referer

Utilisez curl pour tester :
```bash
curl -X POST -H "Referer: https://evil.com" -d "identifiant=admin&code_acces=password" https://examen.pythonanywhere.com/auth/connexion/
```

La requête devrait être rejetée.

### 4. Sécurités supplémentaires recommandées

#### 4.1. Changer le mot de passe admin

Connectez-vous à votre base de données et changez le mot de passe admin :

```python
# Dans le shell PythonAnywhere
python manage.py shell
```

```python
from comptes.models import Utilisateur
admin = Utilisateur.objects.get(username='votre_admin')
admin.set_password('nouveau_mot_de_passe_tres_fort')
admin.save()
```

#### 4.2. Désactiver django-admin (optionnel)

Si vous n'utilisez pas l'admin Django par défaut, désactivez-le :

Dans `config/urls.py`, commentez cette ligne :
```python
# path('django-admin/', admin.site.urls),
```

Dans `config/settings.py`, commentez cette ligne :
```python
# 'django.contrib.admin',
```

### 5. Monitoring

Surveillez les logs PythonAnywhere pour détecter toute activité suspecte :
- Allez dans "Web" → votre application → "Logs"

### 6. Rollback en cas de problème

Si quelque chose ne fonctionne pas après déploiement :

```bash
git revert HEAD
git push
```

Puis rechargez l'application sur PythonAnywhere.
