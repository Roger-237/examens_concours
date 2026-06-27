from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from comptes.middleware import EleveRequis
from examens.models import Ecole, Filiere, Epreuve, Tentative, Question, ReponseEleve, Choix
from comptes.models import CodeParrainage, Parrainage, Notification


# ─────────────────────────────────────────
#  TABLEAU DE BORD ÉLÈVE
# ─────────────────────────────────────────
class VueTableauDeBord(EleveRequis, View):

    def get(self, request):
        eleve = request.user.eleve
        notifications = Notification.objects.filter(
            destinataire=request.user,
            lue=False
        ).order_by('-date')[:5]

        contexte = {
            'eleve'            : eleve,
            'total_tentatives' : Tentative.objects.filter(eleve=eleve, terminee=True).count(),
            'notifications'    : notifications,
            'total_parrainages': Parrainage.objects.filter(parrain=eleve).count(),
        }
        return render(request, 'examens/eleve/tableau_de_bord.html', contexte)


# ─────────────────────────────────────────
#  ÉTAPE 1 — CHOISIR UNE ÉCOLE
# ─────────────────────────────────────────
class VueChoisirEcole(EleveRequis, View):

    def get(self, request):
        ecoles = Ecole.objects.all()
        return render(request, 'examens/eleve/choisir_ecole.html', {'ecoles': ecoles})


# ─────────────────────────────────────────
#  ÉTAPE 2 — CHOISIR UNE FILIÈRE
# ─────────────────────────────────────────
class VueChoisirFiliere(EleveRequis, View):

    def get(self, request, ecole_id):
        ecole = get_object_or_404(Ecole, id=ecole_id)
        filieres = ecole.filieres.all()
        return render(request, 'examens/eleve/choisir_filiere.html', {
            'ecole': ecole,
            'filieres': filieres,
        })


# ─────────────────────────────────────────
#  ÉTAPE 3 — CHOISIR UNE ÉPREUVE
# ─────────────────────────────────────────
class VueChoisirEpreuve(EleveRequis, View):

    def get(self, request, filiere_id):
        filiere = get_object_or_404(Filiere, id=filiere_id)
        epreuves = filiere.epreuves.all()
        return render(request, 'examens/eleve/choisir_epreuve.html', {
            'filiere': filiere,
            'epreuves': epreuves,
        })


# ─────────────────────────────────────────
#  ÉTAPE 4 — MINI COURS
# ─────────────────────────────────────────
class VueMiniCours(EleveRequis, View):

    def get(self, request, epreuve_id):
        epreuve = get_object_or_404(Epreuve, id=epreuve_id)

        if epreuve.questions.count() == 0:
            messages.error(request, "Cette épreuve ne contient pas encore de questions.")
            return redirect('eleve:choisir_epreuve', filiere_id=epreuve.filiere.id)

        return render(request, 'examens/eleve/mini_cours.html', {'epreuve': epreuve})


# ─────────────────────────────────────────
#  DÉMARRER UN EXAMEN
# ─────────────────────────────────────────
class VueDemarrerExamen(EleveRequis, View):

    def get(self, request, epreuve_id):
        epreuve = get_object_or_404(Epreuve, id=epreuve_id)
        eleve = request.user.eleve

        # Crée une nouvelle tentative
        tentative = Tentative.objects.create(eleve=eleve, epreuve=epreuve)

        return redirect('eleve:passer_question', tentative_id=tentative.id, ordre=1)


# ─────────────────────────────────────────
#  PASSER UNE QUESTION
# ─────────────────────────────────────────
class VuePasserQuestion(EleveRequis, View):

    def get(self, request, tentative_id, ordre):
        tentative = get_object_or_404(Tentative, id=tentative_id, eleve=request.user.eleve)

        if tentative.terminee:
            return redirect('eleve:resultat_examen', tentative_id=tentative.id)

        questions = list(tentative.epreuve.questions.prefetch_related('choix').all())
        total_questions = len(questions)

        if int(ordre) > total_questions:
            return redirect('eleve:terminer_examen', tentative_id=tentative.id)

        question = questions[int(ordre) - 1]

        return render(request, 'examens/eleve/passer_question.html', {
            'tentative': tentative,
            'question': question,
            'ordre': int(ordre),
            'total_questions': total_questions,
        })

    def post(self, request, tentative_id, ordre):
        tentative = get_object_or_404(Tentative, id=tentative_id, eleve=request.user.eleve)
        questions = list(tentative.epreuve.questions.all())
        question = questions[int(ordre) - 1]

        choix_id = request.POST.get('choix')
        choix = None
        if choix_id:
            choix = Choix.objects.filter(id=choix_id, question=question).first()

        # Enregistre la réponse (une seule fois par question)
        ReponseEleve.objects.update_or_create(
            tentative=tentative,
            question=question,
            defaults={'choix': choix},
        )

        ordre_suivant = int(ordre) + 1
        if ordre_suivant > len(questions):
            return redirect('eleve:terminer_examen', tentative_id=tentative.id)

        return redirect('eleve:passer_question', tentative_id=tentative.id, ordre=ordre_suivant)


# ─────────────────────────────────────────
#  TERMINER L'EXAMEN — calcul du score
# ─────────────────────────────────────────
class VueTerminerExamen(EleveRequis, View):

    def get(self, request, tentative_id):
        tentative = get_object_or_404(Tentative, id=tentative_id, eleve=request.user.eleve)

        if not tentative.terminee:
            score = 0
            for reponse in tentative.reponses.select_related('choix', 'question'):
                if reponse.choix is None:
                    continue  # pas répondu → 0
                if reponse.choix.est_correct:
                    score += 1
                else:
                    score -= 1

            tentative.score = score
            tentative.terminee = True
            tentative.date_fin = timezone.now()
            tentative.save()

        return redirect('eleve:resultat_examen', tentative_id=tentative.id)


# ─────────────────────────────────────────
#  MES RÉSULTATS — historique
# ─────────────────────────────────────────
class VueMesResultats(EleveRequis, View):

    def get(self, request):
        eleve = request.user.eleve
        tentatives = Tentative.objects.filter(
            eleve=eleve, terminee=True
        ).select_related('epreuve', 'epreuve__filiere', 'epreuve__filiere__ecole').order_by('-date_fin')

        return render(request, 'examens/eleve/mes_resultats.html', {
            'tentatives': tentatives,
        })


# ─────────────────────────────────────────
#  RÉSULTAT + CORRECTIONS
# ─────────────────────────────────────────
class VueResultatExamen(EleveRequis, View):

    def get(self, request, tentative_id):
        tentative = get_object_or_404(
            Tentative.objects.select_related('epreuve'),
            id=tentative_id, eleve=request.user.eleve
        )

        questions = tentative.epreuve.questions.prefetch_related('choix').all()
        reponses = {r.question_id: r.choix_id for r in tentative.reponses.all()}

        details = []
        for question in questions:
            choix_eleve_id = reponses.get(question.id)
            choix_correct = question.choix.filter(est_correct=True).first()
            details.append({
                'question': question,
                'choix_eleve_id': choix_eleve_id,
                'choix_correct': choix_correct,
            })

        total_questions = questions.count()

        return render(request, 'examens/eleve/resultat_examen.html', {
            'tentative': tentative,
            'details': details,
            'total_questions': total_questions,
        })


# ─────────────────────────────────────────
#  GÉNÉRER CODE PARRAINAGE
# ─────────────────────────────────────────
class VueGenererCodeParrainage(EleveRequis, View):

    def post(self, request):
        eleve = request.user.eleve

        if hasattr(eleve, 'code_parrainage'):
            messages.info(request, f'Votre code parrainage est déjà : {eleve.code_parrainage.code}')
            return redirect('eleve:tableau_de_bord')

        # Génère un code unique
        code = CodeParrainage.generer_code(eleve.nom_complet)
        while CodeParrainage.objects.filter(code=code).exists():
            code = CodeParrainage.generer_code(eleve.nom_complet)

        CodeParrainage.objects.create(eleve=eleve, code=code)
        messages.success(request, f'Votre code parrainage a été généré : {code}')
        return redirect('eleve:tableau_de_bord')


# ─────────────────────────────────────────
#  MES PARRAINAGES
# ─────────────────────────────────────────
class VueMesParrainages(EleveRequis, View):

    def get(self, request):
        eleve      = request.user.eleve
        parrainages = Parrainage.objects.filter(parrain=eleve).select_related('filleul').order_by('-date')
        total       = parrainages.count()
        bonus_atteint = total >= 5

        # Marquer notifications comme lues
        Notification.objects.filter(
            destinataire=request.user,
            lue=False
        ).update(lue=True)

        return render(request, 'examens/eleve/mes_parrainages.html', {
            'parrainages'  : parrainages,
            'total'        : total,
            'bonus_atteint': bonus_atteint,
            'progression'  : min(total, 5),
        })