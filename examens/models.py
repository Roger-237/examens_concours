import uuid
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────
#  ÉCOLE
# ─────────────────────────────────────────
class Ecole(models.Model):

    nom  = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    logo = models.ImageField(upload_to='ecoles/logos/', blank=True, null=True, verbose_name='Logo')

    class Meta:
        verbose_name        = 'École'
        verbose_name_plural = 'Écoles'
        ordering            = ['nom']

    def __str__(self):
        return self.nom


# ─────────────────────────────────────────
#  FILIÈRE
# ─────────────────────────────────────────
class Filiere(models.Model):

    nom   = models.CharField(max_length=100, verbose_name='Nom')
    ecole = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='filieres')

    class Meta:
        verbose_name        = 'Filière'
        verbose_name_plural = 'Filières'
        ordering            = ['nom']
        unique_together     = ['nom', 'ecole']

    def __str__(self):
        return f"{self.nom} — {self.ecole.nom}"


# ─────────────────────────────────────────
#  ÉPREUVE
# ─────────────────────────────────────────
class Epreuve(models.Model):

    filiere    = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='epreuves')
    titre      = models.CharField(max_length=200, verbose_name='Titre')
    annee      = models.PositiveIntegerField(verbose_name='Année')
    mini_cours = models.TextField(verbose_name='Mini cours', blank=True)

    class Meta:
        verbose_name        = 'Épreuve'
        verbose_name_plural = 'Épreuves'
        ordering            = ['-annee']
        unique_together     = ['filiere', 'titre', 'annee']

    def __str__(self):
        return f"{self.titre} — {self.annee} ({self.filiere.nom})"


# ─────────────────────────────────────────
#  QUESTION
# ─────────────────────────────────────────
class Question(models.Model):

    epreuve = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='questions')
    texte   = models.TextField(verbose_name='Texte de la question')
    image   = models.ImageField(upload_to='questions/', null=True, blank=True, verbose_name='Image')
    ordre   = models.PositiveIntegerField(verbose_name='Ordre', default=1)

    class Meta:
        verbose_name        = 'Question'
        verbose_name_plural = 'Questions'
        ordering            = ['ordre']

    def __str__(self):
        return f"Q{self.ordre} — {self.epreuve.titre}"


# ─────────────────────────────────────────
#  CHOIX
# ─────────────────────────────────────────
class Choix(models.Model):

    question    = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choix')
    texte       = models.CharField(max_length=500, verbose_name='Texte')
    est_correct = models.BooleanField(default=False, verbose_name='Correct')

    class Meta:
        verbose_name        = 'Choix'
        verbose_name_plural = 'Choix'

    def __str__(self):
        return f"{'✓' if self.est_correct else '✗'} {self.texte}"


# ─────────────────────────────────────────
#  TENTATIVE
# ─────────────────────────────────────────
class Tentative(models.Model):

    eleve      = models.ForeignKey('comptes.Eleve', on_delete=models.CASCADE, related_name='tentatives')
    epreuve    = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='tentatives')
    score      = models.IntegerField(default=0, verbose_name='Score')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin   = models.DateTimeField(null=True, blank=True)
    terminee   = models.BooleanField(default=False)

    class Meta:
        verbose_name        = 'Tentative'
        verbose_name_plural = 'Tentatives'
        ordering            = ['-date_debut']

    def __str__(self):
        return f"{self.eleve.nom_complet} — {self.epreuve.titre} ({self.score}pts)"


# ─────────────────────────────────────────
#  RÉPONSE ÉLÈVE
# ─────────────────────────────────────────
class ReponseEleve(models.Model):

    tentative = models.ForeignKey(Tentative, on_delete=models.CASCADE, related_name='reponses')
    question  = models.ForeignKey(Question, on_delete=models.CASCADE)
    choix     = models.ForeignKey(Choix, on_delete=models.SET_NULL, null=True, blank=True)
    # null = pas répondu dans les 10s → score 0

    class Meta:
        verbose_name        = 'Réponse élève'
        verbose_name_plural = 'Réponses élèves'
        unique_together     = ['tentative', 'question']

    def __str__(self):
        return f"{self.tentative.eleve.nom_complet} — Q{self.question.ordre}"


# ─────────────────────────────────────────
#  CONCOURS BLANC
# ─────────────────────────────────────────
class ConcoursBlanc(models.Model):

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('publie',    'Publié'),
        ('termine',    'Terminé'),
    ]

    ecole             = models.ForeignKey(Ecole, on_delete=models.CASCADE, related_name='concours_blancs')
    titre             = models.CharField(max_length=200, verbose_name='Titre')
    heure_debut       = models.DateTimeField(verbose_name='Heure de début')
    heure_fin         = models.DateTimeField(verbose_name='Heure de fin')
    nb_places_max     = models.PositiveIntegerField(verbose_name='Nombre de places maximum')
    statut            = models.CharField(max_length=15, choices=STATUT_CHOICES, default='brouillon', verbose_name='Statut')
    classement_publie = models.BooleanField(default=False, verbose_name='Classement publié')
    date_creation     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Concours Blanc'
        verbose_name_plural = 'Concours Blancs'
        ordering            = ['-date_creation']

    def __str__(self):
        return f"{self.titre} ({self.ecole.nom}) — {self.get_statut_display()}"

    def est_ouvert(self):
        maintenant = timezone.now()
        return self.statut == 'publie' and self.heure_debut <= maintenant <= self.heure_fin

    def places_restantes(self):
        return max(0, self.nb_places_max - self.participants.count())


class ConcoursBlancEpreuve(models.Model):

    concours = models.ForeignKey(ConcoursBlanc, on_delete=models.CASCADE, related_name='concours_epreuves')
    epreuve  = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='epreuves_concours')
    ordre    = models.PositiveIntegerField(default=1, verbose_name='Ordre')

    class Meta:
        verbose_name        = 'Épreuve du concours blanc'
        verbose_name_plural = 'Épreuves du concours blanc'
        ordering            = ['ordre']
        unique_together     = [('concours', 'epreuve'), ('concours', 'ordre')]

    def __str__(self):
        return f"{self.concours.titre} — Épreuve {self.ordre} : {self.epreuve.titre}"


class ParticipantConcours(models.Model):

    concours         = models.ForeignKey(ConcoursBlanc, on_delete=models.CASCADE, related_name='participants')
    nom              = models.CharField(max_length=150, verbose_name='Nom du participant')
    token            = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Participant concours blanc'
        verbose_name_plural = 'Participants concours blanc'
        ordering            = ['date_inscription']
        unique_together     = ['concours', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.concours.titre})"

    @property
    def score_total(self):
        return sum(t.score for t in self.tentatives.filter(terminee=True))


class TentativeConcoursParticipant(models.Model):

    participant = models.ForeignKey(ParticipantConcours, on_delete=models.CASCADE, related_name='tentatives')
    epreuve     = models.ForeignKey(Epreuve, on_delete=models.CASCADE, related_name='tentatives_concours')
    score       = models.IntegerField(default=0, verbose_name='Score')
    date_debut  = models.DateTimeField(auto_now_add=True)
    date_fin    = models.DateTimeField(null=True, blank=True)
    terminee    = models.BooleanField(default=False)
    revue       = models.BooleanField(default=False, verbose_name='Revue')

    class Meta:
        verbose_name        = 'Tentative concours participant'
        verbose_name_plural = 'Tentatives concours participant'
        unique_together     = ['participant', 'epreuve']

    def __str__(self):
        return f"{self.participant.nom} — {self.epreuve.titre} ({self.score}pts)"


class ReponseConcoursParticipant(models.Model):

    tentative = models.ForeignKey(TentativeConcoursParticipant, on_delete=models.CASCADE, related_name='reponses')
    question  = models.ForeignKey(Question, on_delete=models.CASCADE)
    choix     = models.ForeignKey(Choix, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name        = 'Réponse concours participant'
        verbose_name_plural = 'Réponses concours participant'
        unique_together     = ['tentative', 'question']

    def __str__(self):
        return f"{self.tentative.participant.nom} — Q{self.question.ordre}"
