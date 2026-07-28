import threading
from datetime import timedelta
from django.db import connection
from django.test import TestCase, TransactionTestCase, Client
from django.utils import timezone
from django.urls import reverse
from examens.models import (
    Ecole, Filiere, Epreuve, Question, Choix,
    ConcoursBlanc, ConcoursBlancEpreuve, ParticipantConcours,
    TentativeConcoursParticipant, ReponseConcoursParticipant
)


class ConcoursBlancTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.ecole = Ecole.objects.create(nom="INPTIC Test")
        self.filiere = Filiere.objects.create(nom="Informatique", ecole=self.ecole)

        # Création de 3 épreuves avec 2 questions chacune
        self.epreuve1 = Epreuve.objects.create(filiere=self.filiere, titre="Épreuve 1", annee=2026)
        self.epreuve2 = Epreuve.objects.create(filiere=self.filiere, titre="Épreuve 2", annee=2026)
        self.epreuve3 = Epreuve.objects.create(filiere=self.filiere, titre="Épreuve 3", annee=2026)

        # Questions pour Epreuve 1
        self.q1_1 = Question.objects.create(epreuve=self.epreuve1, texte="Q1 E1", ordre=1)
        self.c1_1_v = Choix.objects.create(question=self.q1_1, texte="Vrai", est_correct=True)
        self.c1_1_f = Choix.objects.create(question=self.q1_1, texte="Faux", est_correct=False)

        self.q1_2 = Question.objects.create(epreuve=self.epreuve1, texte="Q2 E1", ordre=2)
        self.c1_2_v = Choix.objects.create(question=self.q1_2, texte="Vrai", est_correct=True)

        # Questions pour Epreuve 2
        self.q2_1 = Question.objects.create(epreuve=self.epreuve2, texte="Q1 E2", ordre=1)
        self.c2_1_v = Choix.objects.create(question=self.q2_1, texte="Vrai", est_correct=True)

        # Questions pour Epreuve 3
        self.q3_1 = Question.objects.create(epreuve=self.epreuve3, texte="Q1 E3", ordre=1)
        self.c3_1_v = Choix.objects.create(question=self.q3_1, texte="Vrai", est_correct=True)

        # Concours Blanc en direct (début -1h, fin +1h)
        maintenant = timezone.now()
        self.concours = ConcoursBlanc.objects.create(
            ecole=self.ecole,
            titre="Grand Concours Blanc",
            heure_debut=maintenant - timedelta(hours=1),
            heure_fin=maintenant + timedelta(hours=1),
            nb_places_max=2,
            statut='publie',
            classement_publie=False
        )

        ConcoursBlancEpreuve.objects.create(concours=self.concours, epreuve=self.epreuve1, ordre=1)
        ConcoursBlancEpreuve.objects.create(concours=self.concours, epreuve=self.epreuve2, ordre=2)
        ConcoursBlancEpreuve.objects.create(concours=self.concours, epreuve=self.epreuve3, ordre=3)

    def test_1_inscription_nom_doublon_refusee(self):
        """Test 1: Inscription avec un nom déjà pris -> Refusée avec message propre."""
        url = reverse('concours:inscription')
        res1 = self.client.post(url, {'nom': 'Jean Dupont'}, follow=True)
        self.assertEqual(ParticipantConcours.objects.filter(concours=self.concours).count(), 1)

        # Deuxième inscription avec le même nom (insensible à la casse)
        res2 = self.client.post(url, {'nom': 'jean dupont'}, follow=True)
        self.assertEqual(ParticipantConcours.objects.filter(concours=self.concours).count(), 1)
        self.assertContains(res2, "déjà inscrit")

    def test_2_inscription_limite_places_max(self):
        """Test 2: Inscription une fois nb_places_max atteint -> Refusée avec message clair."""
        url = reverse('concours:inscription')
        self.client.post(url, {'nom': 'Participant 1'})
        self.client.post(url, {'nom': 'Participant 2'})

        self.assertEqual(ParticipantConcours.objects.filter(concours=self.concours).count(), 2)

        # Tentative 3 (limite = 2)
        res = self.client.post(url, {'nom': 'Participant 3'}, follow=True)
        self.assertEqual(ParticipantConcours.objects.filter(concours=self.concours).count(), 2)
        self.assertContains(res, "Inscriptions closes")

    def test_3_reprise_token_question_suivante(self):
        """Test 3: Fermeture d'onglet et reprise par token UUID à la bonne question suivante."""
        p = ParticipantConcours.objects.create(concours=self.concours, nom="Alice")
        t1 = TentativeConcoursParticipant.objects.create(participant=p, epreuve=self.epreuve1)

        # Alice répond à la première question
        ReponseConcoursParticipant.objects.create(tentative=t1, question=self.q1_1, choix=self.c1_1_v)

        # Simulation de réouverture du navigateur avec son token direct
        url_passer = reverse('concours:passer_token', kwargs={'token': p.token})
        res = self.client.get(url_passer)

        self.assertEqual(res.status_code, 200)
        # Elle doit se retrouver sur la Question 2 (Q2 E1)
        self.assertContains(res, "Q2 E1")
        self.assertNotContains(res, "Q1 E1")

    def test_4_blocage_apres_heure_fin(self):
        """Test 4: Passé heure_fin, toute inscription ou poursuite d'épreuve est bloquée net."""
        # Avancer le concours dans le passé
        self.concours.heure_fin = timezone.now() - timedelta(minutes=10)
        self.concours.save()

        # Inscription bloquée
        res_insc = self.client.post(reverse('concours:inscription'), {'nom': 'Retardataire'}, follow=True)
        self.assertContains(res_insc, "terminé")
        self.assertEqual(ParticipantConcours.objects.filter(concours=self.concours, nom='Retardataire').count(), 0)

        # Poursuite bloquée pour participant existant
        p = ParticipantConcours.objects.create(concours=self.concours, nom="Bob")
        url_passer = reverse('concours:passer_token', kwargs={'token': p.token})
        res_passer = self.client.get(url_passer, follow=True)
        self.assertRedirects(res_passer, reverse('concours:fin_token', kwargs={'token': p.token}))

    def test_5_classement_invisible_tant_que_non_publie(self):
        """Test 5: Classement reste masqué tant que classement_publie=False, visible si True."""
        url_classement = reverse('concours:classement')

        # classement_publie = False
        res_masque = self.client.get(url_classement)
        self.assertContains(res_masque, "non encore publié")

        # Admin active la publication
        self.concours.classement_publie = True
        self.concours.save()

        res_publie = self.client.get(url_classement)
        self.assertContains(res_publie, "Classement Officiel Publié")


class ConcoursBlancConcurrencyTestCase(TransactionTestCase):

    def test_6_concurrence_select_for_update_places_max(self):
        """Test 6: Simulation de 2 inscriptions simultanées proches de la limite nb_places_max."""
        ecole = Ecole.objects.create(nom="INPTIC Concurrency")
        c_limite = ConcoursBlanc.objects.create(
            ecole=ecole,
            titre="Concours 1 Place",
            heure_debut=timezone.now() - timedelta(hours=1),
            heure_fin=timezone.now() + timedelta(hours=1),
            nb_places_max=1,
            statut='publie',
        )

        def inscrire(nom):
            client = Client()
            client.post(reverse('concours:inscription'), {'nom': nom})
            connection.close()

        t1 = threading.Thread(target=inscrire, args=('Concurrent A',))
        t2 = threading.Thread(target=inscrire, args=('Concurrent B',))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Vérification qu'exactement 1 seul participant est inscrit
        self.assertEqual(ParticipantConcours.objects.filter(concours=c_limite).count(), 1)


