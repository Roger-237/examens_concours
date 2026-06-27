from django.db import models


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