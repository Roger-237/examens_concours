from django.test import TestCase
from django.db import models
from examens.models import Epreuve, Question, Ecole, Filiere
from scripts.importer_epreuves import nettoyer_latex

class QuestionModelTest(TestCase):
    def setUp(self):
        self.ecole = Ecole.objects.create(nom="Ecole Test")
        self.filiere = Filiere.objects.create(nom="Filiere Test", ecole=self.ecole)
        self.epreuve = Epreuve.objects.create(filiere=self.filiere, titre="Epreuve Test", annee=2026)

    def test_question_has_image_field(self):
        question = Question.objects.create(
            epreuve=self.epreuve,
            texte="Quelle est la réponse ?",
            ordre=1
        )
        # Check that the field exists and accepts an image path
        self.assertTrue(hasattr(question, 'image'))
        question.image = 'questions/test_image.png'
        question.save()
        
        q_refreshed = Question.objects.get(pk=question.pk)
        self.assertEqual(q_refreshed.image, 'questions/test_image.png')

    def test_nettoyer_latex(self):
        text = r"Calculer $\int_0^\infty e^{-x} dx$"
        self.assertEqual(nettoyer_latex(text), text)
