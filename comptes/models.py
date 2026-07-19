from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
import string


# ─────────────────────────────────────────
#  RÔLES
# ─────────────────────────────────────────
class Role(models.TextChoices):
    ADMIN = 'admin', 'Administrateur'
    ELEVE = 'eleve', 'Élève'


# ─────────────────────────────────────────
#  GESTIONNAIRE UTILISATEUR
# ─────────────────────────────────────────
class GestionnaireUtilisateur(BaseUserManager):

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Le nom d\'utilisateur est obligatoire')
        utilisateur = self.model(username=username, **extra_fields)
        utilisateur.set_password(password)
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('role',         Role.ADMIN)
        extra_fields.setdefault('is_staff',     True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active',    True)
        return self.create_user(username, password, **extra_fields)


# ─────────────────────────────────────────
#  UTILISATEUR
# ─────────────────────────────────────────
class Utilisateur(AbstractBaseUser, PermissionsMixin):

    username          = models.CharField(max_length=150, unique=True, verbose_name='Nom d\'utilisateur')
    role              = models.CharField(max_length=10, choices=Role.choices, default=Role.ELEVE, verbose_name='Rôle')
    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    date_inscription  = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = []

    objects = GestionnaireUtilisateur()

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='Groupes',
        blank=True,
        related_name='utilisateurs',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='Permissions',
        blank=True,
        related_name='utilisateurs',
    )

    class Meta:
        verbose_name        = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering            = ['-date_inscription']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# ─────────────────────────────────────────
#  ÉLÈVE
# ─────────────────────────────────────────
def generer_code_acces(nom_complet):
    """
    Génère un code lisible et mémorable :
    ex: NZANGessone2026#47
    (Nom de famille en majuscules + prénom en minuscules + année + caractère spécial + 2 chiffres aléatoires)
    """
    parties = nom_complet.strip().split()
    if len(parties) >= 2:
        famille = ''.join(ch for ch in parties[0] if ch.isalpha()).upper()
        prenom  = ''.join(ch for ch in parties[1] if ch.isalpha()).lower()
    else:
        mot = ''.join(ch for ch in parties[0] if ch.isalpha())
        milieu = max(1, len(mot) // 2)
        famille = mot[:milieu].upper()
        prenom  = mot[milieu:].lower()

    annee    = timezone.now().year
    special  = random.choice('#@$*!?')
    suffixe  = ''.join(random.choices(string.digits, k=2))

    # Limiter la longueur totale à 20 caractères (famille + prenom <= 13)
    max_name_length = 13
    if len(famille) + len(prenom) > max_name_length:
        # Tronquer le nom de famille en priorité
        available_for_famille = max(1, max_name_length - len(prenom))
        famille = famille[:available_for_famille]

    return f"{famille}{prenom}{annee}{special}{suffixe}"


class Eleve(models.Model):

    utilisateur      = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='eleve')
    nom_complet      = models.CharField(max_length=200, verbose_name='Nom complet')
    code_acces       = models.CharField(max_length=20, unique=True, verbose_name='Code d\'accès')
    statut           = models.CharField(
                           max_length=10,
                           choices=[('actif', 'Actif'), ('suspendu', 'Suspendu')],
                           default='actif',
                           verbose_name='Statut'
                       )
    empreinte_device = models.CharField(max_length=255, blank=True, verbose_name='Empreinte appareil')
    date_inscription = models.DateTimeField(auto_now_add=True, verbose_name='Date d\'inscription')

    class Meta:
        verbose_name        = 'Élève'
        verbose_name_plural = 'Élèves'
        ordering            = ['-date_inscription']

    def __str__(self):
        return f"{self.nom_complet} ({self.code_acces})"

    def est_suspendu(self):
        return self.statut == 'suspendu'


# ─────────────────────────────────────────
#  CODE PARRAINAGE
# ─────────────────────────────────────────
class CodeParrainage(models.Model):

    eleve      = models.OneToOneField(Eleve, on_delete=models.CASCADE, related_name='code_parrainage')
    code       = models.CharField(max_length=50, unique=True, verbose_name='Code parrainage')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Code parrainage'
        verbose_name_plural = 'Codes parrainage'

    def __str__(self):
        return f"{self.code} — {self.eleve.nom_complet}"

    @staticmethod
    def generer_code(nom_complet):
        """Génère un code unique : jeandupont2026XX"""
        from django.utils import timezone
        import random
        base    = nom_complet.lower().replace(' ', '')[:10]
        annee   = timezone.now().year
        suffixe = random.randint(10, 99)
        return f"{base}{annee}{suffixe}"


# ─────────────────────────────────────────
#  PARRAINAGE
# ─────────────────────────────────────────
class Parrainage(models.Model):

    parrain    = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='parrainages_effectues')
    filleul    = models.ForeignKey(Eleve, on_delete=models.CASCADE, related_name='parrainage_recu')
    date       = models.DateTimeField(auto_now_add=True)
    bonus_paye = models.BooleanField(default=False, verbose_name='Bonus payé')

    class Meta:
        verbose_name        = 'Parrainage'
        verbose_name_plural = 'Parrainages'
        unique_together     = ['parrain', 'filleul']

    def __str__(self):
        return f"{self.parrain.nom_complet} → {self.filleul.nom_complet}"


# ─────────────────────────────────────────
#  NOTIFICATION
# ─────────────────────────────────────────
class Notification(models.Model):

    TYPES = [
        ('parrainage', 'Parrainage'),
        ('bonus',      'Bonus'),
        ('info',       'Information'),
    ]

    destinataire = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='notifications')
    type_notif   = models.CharField(max_length=20, choices=TYPES, default='info')
    message      = models.TextField()
    lue          = models.BooleanField(default=False)
    date         = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering            = ['-date']

    def __str__(self):
        return f"{self.destinataire.username} — {self.message[:50]}"


# ─────────────────────────────────────────
#  MIGRATION TRANSPARENTE DES CODES D'ACCÈS
# ─────────────────────────────────────────
class MigrationCodeAcces(models.Model):
    """Table temporaire : nouveau code déjà préparé, en attente d'activation
       à la prochaine connexion réussie de l'élève."""
    eleve         = models.OneToOneField(Eleve, on_delete=models.CASCADE, related_name='migration_code')
    ancien_code   = models.CharField(max_length=20)
    nouveau_code  = models.CharField(max_length=20)
    migre         = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_migre    = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name        = 'Migration code d\'accès'
        verbose_name_plural = 'Migrations codes d\'accès'

    def __str__(self):
        return f"{self.eleve.nom_complet}: {self.ancien_code} -> {self.nouveau_code} (migré={self.migre})"