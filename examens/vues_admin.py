from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from comptes.middleware import AdminRequis
from comptes.models import Eleve, Utilisateur, Role, generer_code_acces, Parrainage, Notification
from examens.models import (
    Ecole, Epreuve, ConcoursBlanc, ConcoursBlancEpreuve,
    ParticipantConcours, TentativeConcoursParticipant
)
from examens.formulaires import FormulaireEcole, FormulaireConcoursBlanc


# ─────────────────────────────────────────
#  TABLEAU DE BORD ADMIN
# ─────────────────────────────────────────
class VueTableauDeBord(AdminRequis, View):

    def get(self, request):
        from django.db.models import Count
        bonus_en_attente = Eleve.objects.annotate(
            nb=Count('parrainages_effectues')
        ).filter(nb__gte=5, parrainages_effectues__bonus_paye=False).distinct().count()

        notifications = Notification.objects.filter(
            destinataire=request.user,
            lue=False
        ).order_by('-date')[:5]

        contexte = {
            'total_ecoles'      : Ecole.objects.count(),
            'total_epreuves'    : Epreuve.objects.count(),
            'total_eleves'      : Eleve.objects.count(),
            'eleves_suspendus'  : Eleve.objects.filter(statut='suspendu').count(),
            'bonus_en_attente'  : bonus_en_attente,
            'notifications'     : notifications,
        }
        return render(request, 'examens/admin/tableau_de_bord.html', contexte)


# ─────────────────────────────────────────
#  LISTE DES ÉCOLES
# ─────────────────────────────────────────
class VueListeEcoles(AdminRequis, View):

    def get(self, request):
        ecoles = Ecole.objects.all()
        return render(request, 'examens/admin/ecoles_liste.html', {'ecoles': ecoles})


# ─────────────────────────────────────────
#  AJOUTER UNE ÉCOLE
# ─────────────────────────────────────────
class VueAjouterEcole(AdminRequis, View):

    def get(self, request):
        formulaire = FormulaireEcole()
        return render(request, 'examens/admin/ecole_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une école',
        })

    def post(self, request):
        formulaire = FormulaireEcole(request.POST, request.FILES)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, 'École ajoutée avec succès.')
            return redirect('admin_examens:ecoles_liste')
        return render(request, 'examens/admin/ecole_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une école',
        })


# ─────────────────────────────────────────
#  MODIFIER UNE ÉCOLE
# ─────────────────────────────────────────
class VueModifierEcole(AdminRequis, View):

    def get(self, request, ecole_id):
        ecole      = get_object_or_404(Ecole, id=ecole_id)
        formulaire = FormulaireEcole(instance=ecole)
        return render(request, 'examens/admin/ecole_form.html', {
            'form': formulaire,
            'titre': 'Modifier l\'école',
        })

    def post(self, request, ecole_id):
        ecole      = get_object_or_404(Ecole, id=ecole_id)
        formulaire = FormulaireEcole(request.POST, request.FILES, instance=ecole)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, 'École modifiée avec succès.')
            return redirect('admin_examens:ecoles_liste')
        return render(request, 'examens/admin/ecole_form.html', {
            'form': formulaire,
            'titre': 'Modifier l\'école',
        })


# ─────────────────────────────────────────
#  SUPPRIMER UNE ÉCOLE
# ─────────────────────────────────────────
class VueSupprimerEcole(AdminRequis, View):

    def post(self, request, ecole_id):
        ecole = get_object_or_404(Ecole, id=ecole_id)
        ecole.delete()
        messages.success(request, 'École supprimée avec succès.')
        return redirect('admin_examens:ecoles_liste')

from examens.models import Ecole, Epreuve, Filiere, Question, Choix
from examens.formulaires import (
    FormulaireEcole, FormulaireFiliere, FormulaireEpreuve,
    FormulaireQuestion, ChoixFormSet, FormulaireEleve
)


# ─────────────────────────────────────────
#  LISTE DES FILIÈRES
# ─────────────────────────────────────────
class VueListeFilieres(AdminRequis, View):

    def get(self, request):
        filieres = Filiere.objects.select_related('ecole').all()
        return render(request, 'examens/admin/filieres_liste.html', {'filieres': filieres})


# ─────────────────────────────────────────
#  AJOUTER UNE FILIÈRE
# ─────────────────────────────────────────
class VueAjouterFiliere(AdminRequis, View):

    def get(self, request):
        formulaire = FormulaireFiliere()
        return render(request, 'examens/admin/filiere_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une filière',
        })

    def post(self, request):
        formulaire = FormulaireFiliere(request.POST)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, 'Filière ajoutée avec succès.')
            return redirect('admin_examens:filieres_liste')
        return render(request, 'examens/admin/filiere_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une filière',
        })


# ─────────────────────────────────────────
#  MODIFIER UNE FILIÈRE
# ─────────────────────────────────────────
class VueModifierFiliere(AdminRequis, View):

    def get(self, request, filiere_id):
        filiere    = get_object_or_404(Filiere, id=filiere_id)
        formulaire = FormulaireFiliere(instance=filiere)
        return render(request, 'examens/admin/filiere_form.html', {
            'form': formulaire,
            'titre': 'Modifier la filière',
        })

    def post(self, request, filiere_id):
        filiere    = get_object_or_404(Filiere, id=filiere_id)
        formulaire = FormulaireFiliere(request.POST, instance=filiere)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, 'Filière modifiée avec succès.')
            return redirect('admin_examens:filieres_liste')
        return render(request, 'examens/admin/filiere_form.html', {
            'form': formulaire,
            'titre': 'Modifier la filière',
        })


# ─────────────────────────────────────────
#  SUPPRIMER UNE FILIÈRE
# ─────────────────────────────────────────
class VueSupprimerFiliere(AdminRequis, View):

    def post(self, request, filiere_id):
        filiere = get_object_or_404(Filiere, id=filiere_id)
        filiere.delete()
        messages.success(request, 'Filière supprimée avec succès.')
        return redirect('admin_examens:filieres_liste')


# ─────────────────────────────────────────
#  LISTE DES ÉPREUVES
# ─────────────────────────────────────────
class VueListeEpreuves(AdminRequis, View):

    def get(self, request):
        epreuves = Epreuve.objects.select_related('filiere', 'filiere__ecole').all()
        return render(request, 'examens/admin/epreuves_liste.html', {'epreuves': epreuves})


# ─────────────────────────────────────────
#  AJOUTER UNE ÉPREUVE
# ─────────────────────────────────────────
class VueAjouterEpreuve(AdminRequis, View):

    def get(self, request):
        formulaire = FormulaireEpreuve()
        return render(request, 'examens/admin/epreuve_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une épreuve',
        })

    def post(self, request):
        formulaire = FormulaireEpreuve(request.POST)
        if formulaire.is_valid():
            epreuve = formulaire.save()
            messages.success(request, 'Épreuve créée avec succès. Ajoutez maintenant les questions.')
            return redirect('admin_examens:epreuve_questions', epreuve_id=epreuve.id)
        return render(request, 'examens/admin/epreuve_form.html', {
            'form': formulaire,
            'titre': 'Ajouter une épreuve',
        })


# ─────────────────────────────────────────
#  MODIFIER UNE ÉPREUVE
# ─────────────────────────────────────────
class VueModifierEpreuve(AdminRequis, View):

    def get(self, request, epreuve_id):
        epreuve    = get_object_or_404(Epreuve, id=epreuve_id)
        formulaire = FormulaireEpreuve(instance=epreuve)
        return render(request, 'examens/admin/epreuve_form.html', {
            'form': formulaire,
            'titre': 'Modifier l\'épreuve',
            'epreuve': epreuve,
        })

    def post(self, request, epreuve_id):
        epreuve    = get_object_or_404(Epreuve, id=epreuve_id)
        formulaire = FormulaireEpreuve(request.POST, instance=epreuve)
        if formulaire.is_valid():
            formulaire.save()
            messages.success(request, 'Épreuve modifiée avec succès.')
            return redirect('admin_examens:epreuves_liste')
        return render(request, 'examens/admin/epreuve_form.html', {
            'form': formulaire,
            'titre': 'Modifier l\'épreuve',
            'epreuve': epreuve,
        })


# ─────────────────────────────────────────
#  SUPPRIMER UNE ÉPREUVE
# ─────────────────────────────────────────
class VueSupprimerEpreuve(AdminRequis, View):

    def post(self, request, epreuve_id):
        epreuve = get_object_or_404(Epreuve, id=epreuve_id)
        epreuve.delete()
        messages.success(request, 'Épreuve supprimée avec succès.')
        return redirect('admin_examens:epreuves_liste')


# ─────────────────────────────────────────
#  GESTION DES QUESTIONS D'UNE ÉPREUVE
# ─────────────────────────────────────────
class VueQuestionsEpreuve(AdminRequis, View):

    def get(self, request, epreuve_id):
        epreuve   = get_object_or_404(Epreuve, id=epreuve_id)
        questions = epreuve.questions.prefetch_related('choix').all()

        prochain_ordre = (questions.last().ordre + 1) if questions.exists() else 1

        formulaire_question = FormulaireQuestion(initial={'ordre': prochain_ordre})
        formset_choix       = ChoixFormSet(prefix='choix')

        return render(request, 'examens/admin/epreuve_questions.html', {
            'epreuve'             : epreuve,
            'questions'           : questions,
            'formulaire_question' : formulaire_question,
            'formset_choix'       : formset_choix,
        })

    def post(self, request, epreuve_id):
        epreuve = get_object_or_404(Epreuve, id=epreuve_id)

        formulaire_question = FormulaireQuestion(request.POST)

        if formulaire_question.is_valid():
            question     = formulaire_question.save(commit=False)
            question.epreuve = epreuve
            question.save()

            formset_choix = ChoixFormSet(request.POST, instance=question, prefix='choix')

            if formset_choix.is_valid():
                # Vérifier qu'au moins un choix est correct
                choix_corrects = sum(
                    1 for f in formset_choix
                    if f.cleaned_data.get('est_correct') and not f.cleaned_data.get('DELETE')
                )

                if choix_corrects == 0:
                    question.delete()
                    messages.error(request, 'Vous devez cocher au moins une bonne réponse.')
                else:
                    formset_choix.save()
                    messages.success(request, f'Question {question.ordre} ajoutée avec succès.')
                    return redirect('admin_examens:epreuve_questions', epreuve_id=epreuve.id)
            else:
                question.delete()
                messages.error(request, 'Erreur dans les choix de réponse.')
        else:
            messages.error(request, 'Erreur dans le formulaire de question.')

        # Réaffichage en cas d'erreur
        questions = epreuve.questions.prefetch_related('choix').all()
        prochain_ordre = (questions.last().ordre + 1) if questions.exists() else 1

        return render(request, 'examens/admin/epreuve_questions.html', {
            'epreuve'             : epreuve,
            'questions'           : questions,
            'formulaire_question' : FormulaireQuestion(initial={'ordre': prochain_ordre}),
            'formset_choix'       : ChoixFormSet(prefix='choix'),
        })


# ─────────────────────────────────────────
#  SUPPRIMER UNE QUESTION
# ─────────────────────────────────────────
class VueSupprimerQuestion(AdminRequis, View):

    def post(self, request, epreuve_id, question_id):
        question = get_object_or_404(Question, id=question_id, epreuve_id=epreuve_id)
        question.delete()
        messages.success(request, 'Question supprimée avec succès.')
        return redirect('admin_examens:epreuve_questions', epreuve_id=epreuve_id)


# ─────────────────────────────────────────
#  LISTE DES ÉLÈVES
# ─────────────────────────────────────────
class VueListeEleves(AdminRequis, View):

    def get(self, request):
        filtre = request.GET.get('filtre')

        if filtre == 'suspendus':
            eleves = Eleve.objects.select_related('utilisateur').filter(statut='suspendu')
        else:
            eleves = Eleve.objects.select_related('utilisateur').all()

        return render(request, 'examens/admin/eleves_liste.html', {
            'eleves': eleves,
            'filtre': filtre,
        })


# ─────────────────────────────────────────
#  AJOUTER UN ÉLÈVE
# ─────────────────────────────────────────
class VueAjouterEleve(AdminRequis, View):

    def get(self, request):
        formulaire = FormulaireEleve()
        return render(request, 'examens/admin/eleve_form.html', {'form': formulaire})

    def post(self, request):
        formulaire = FormulaireEleve(request.POST)
        if formulaire.is_valid():
            nom_complet = formulaire.cleaned_data['nom_complet'].strip()

            # ── Génération username + code unique ──
            username = nom_complet.lower().replace(' ', '_')

            # Évite les doublons de username
            base_username = username
            compteur = 1
            while Utilisateur.objects.filter(username=username).exists():
                username = f"{base_username}{compteur}"
                compteur += 1

            # Génère un code d'accès unique
            code_acces = generer_code_acces(nom_complet)
            while Eleve.objects.filter(code_acces=code_acces).exists():
                code_acces = generer_code_acces(nom_complet)

            # Crée l'utilisateur (pas de mot de passe utilisable)
            utilisateur = Utilisateur.objects.create_user(
                username=username,
                password=None,
                role=Role.ELEVE,
            )
            utilisateur.set_unusable_password()
            utilisateur.save()

            # Crée le profil élève
            Eleve.objects.create(
                utilisateur=utilisateur,
                nom_complet=nom_complet,
                code_acces=code_acces,
                statut='actif',
            )

            messages.success(
                request,
                f"Élève créé avec succès. Code d'accès : {code_acces}"
            )
            return redirect('admin_examens:eleves_liste')

        return render(request, 'examens/admin/eleve_form.html', {'form': formulaire})


# ─────────────────────────────────────────
#  SUSPENDRE / RÉACTIVER UN ÉLÈVE
# ─────────────────────────────────────────
class VueBasculerStatutEleve(AdminRequis, View):

    def post(self, request, eleve_id):
        eleve = get_object_or_404(Eleve, id=eleve_id)

        if eleve.statut == 'actif':
            eleve.statut = 'suspendu'
            messages.success(request, f"{eleve.nom_complet} a été suspendu.")
        else:
            eleve.statut = 'actif'
            eleve.empreinte_device = ''  # reset empreinte pour réautoriser
            messages.success(request, f"{eleve.nom_complet} a été réactivé.")

        eleve.save()
        return redirect('admin_examens:eleves_liste')


# ─────────────────────────────────────────
#  SUPPRIMER UN ÉLÈVE
# ─────────────────────────────────────────
class VueSupprimerEleve(AdminRequis, View):

    def post(self, request, eleve_id):
        eleve = get_object_or_404(Eleve, id=eleve_id)
        eleve.utilisateur.delete()  # cascade supprime aussi Eleve
        messages.success(request, 'Élève supprimé avec succès.')
        return redirect('admin_examens:eleves_liste')


# ─────────────────────────────────────────
#  PARRAINAGES — VUE ADMIN
# ─────────────────────────────────────────
class VueParrainagesAdmin(AdminRequis, View):

    def get(self, request):
        parrainages   = Parrainage.objects.select_related('parrain', 'filleul').order_by('-date')
        bonus_a_payer = []

        # Élèves ayant atteint 5 parrainages avec bonus non payé
        from django.db.models import Count
        eleves_bonus = Eleve.objects.annotate(
            nb_parrainages=Count('parrainages_effectues')
        ).filter(nb_parrainages__gte=5, parrainages_effectues__bonus_paye=False).distinct()

        return render(request, 'examens/admin/parrainages.html', {
            'parrainages'  : parrainages,
            'eleves_bonus' : eleves_bonus,
        })


# ─────────────────────────────────────────
#  MARQUER BONUS COMME PAYÉ
# ─────────────────────────────────────────
class VueMarquerBonusPaye(AdminRequis, View):

    def post(self, request, eleve_id):
        eleve = get_object_or_404(Eleve, id=eleve_id)
        Parrainage.objects.filter(parrain=eleve).update(bonus_paye=True)

        # Notifie l'élève
        Notification.objects.create(
            destinataire=eleve.utilisateur,
            type_notif='bonus',
            message='✅ Votre bonus de parrainage de 2500 FCFA a été versé. Merci pour votre fidélité !'
        )

        messages.success(request, f'Bonus marqué comme payé pour {eleve.nom_complet}.')
        return redirect('admin_examens:parrainages')


# ─────────────────────────────────────────
#  FONCTION UTILITAIRE : FINALISATION AUTOMATIQUE
# ─────────────────────────────────────────
def finaliser_tentatives_expirees(concours):
    """
    Finalise automatiquement toute tentative non terminée d'un concours
    dont l'heure de fin est dépassée.
    """
    if timezone.now() > concours.heure_fin:
        tentatives_en_cours = TentativeConcoursParticipant.objects.filter(
            participant__concours=concours,
            terminee=False
        ).select_related('epreuve', 'participant')

        for tentative in tentatives_en_cours:
            reponses = {
                r.question_id: r.choix
                for r in tentative.reponses.select_related('choix').all()
            }
            questions = tentative.epreuve.questions.all()
            score = 0
            for q in questions:
                choix = reponses.get(q.id)
                if choix:
                    if choix.est_correct:
                        score += 1
                    else:
                        score -= 1
            tentative.score = score
            tentative.terminee = True
            tentative.date_fin = concours.heure_fin
            tentative.save()


# ─────────────────────────────────────────
#  CONCOURS BLANC — ADMINISTRATION
# ─────────────────────────────────────────
class VueListeConcoursBlanc(AdminRequis, View):

    def get(self, request):
        concours_list = ConcoursBlanc.objects.select_related('ecole').prefetch_related('participants').all()
        return render(request, 'examens/admin/concours_liste.html', {'concours_list': concours_list})


class VueAjouterConcoursBlanc(AdminRequis, View):

    def get(self, request):
        formulaire = FormulaireConcoursBlanc()
        return render(request, 'examens/admin/concours_form.html', {
            'form': formulaire,
            'titre': 'Créer un concours blanc',
        })

    def post(self, request):
        formulaire = FormulaireConcoursBlanc(request.POST)
        if formulaire.is_valid():
            concours = formulaire.save(commit=False)
            concours.statut = 'brouillon'
            concours.save()

            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_1'], ordre=1)
            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_2'], ordre=2)
            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_3'], ordre=3)

            messages.success(request, 'Concours blanc créé avec succès en statut brouillon.')
            return redirect('admin_examens:concours_liste')

        return render(request, 'examens/admin/concours_form.html', {
            'form': formulaire,
            'titre': 'Créer un concours blanc',
        })


class VueModifierConcoursBlanc(AdminRequis, View):

    def get(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)
        epreuves_ord = list(concours.concours_epreuves.order_by('ordre'))

        initial = {}
        if len(epreuves_ord) >= 3:
            initial['epreuve_1'] = epreuves_ord[0].epreuve
            initial['epreuve_2'] = epreuves_ord[1].epreuve
            initial['epreuve_3'] = epreuves_ord[2].epreuve

        formulaire = FormulaireConcoursBlanc(instance=concours, initial=initial)
        return render(request, 'examens/admin/concours_form.html', {
            'form': formulaire,
            'titre': 'Modifier le concours blanc',
            'concours': concours,
        })

    def post(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)
        formulaire = FormulaireConcoursBlanc(request.POST, instance=concours)
        if formulaire.is_valid():
            concours = formulaire.save()
            concours.concours_epreuves.all().delete()

            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_1'], ordre=1)
            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_2'], ordre=2)
            ConcoursBlancEpreuve.objects.create(concours=concours, epreuve=formulaire.cleaned_data['epreuve_3'], ordre=3)

            messages.success(request, 'Concours blanc modifié avec succès.')
            return redirect('admin_examens:concours_liste')

        return render(request, 'examens/admin/concours_form.html', {
            'form': formulaire,
            'titre': 'Modifier le concours blanc',
            'concours': concours,
        })


class VuePublierConcoursBlanc(AdminRequis, View):

    def post(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)
        concours.statut = 'publie'
        concours.save()
        messages.success(request, f'Le concours blanc "{concours.titre}" a été publié.')
        return redirect('admin_examens:concours_liste')


class VueSupprimerConcoursBlanc(AdminRequis, View):

    def post(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)

        titre = concours.titre
        concours.delete()
        messages.success(request, f'Le concours blanc "{titre}" a été supprimé avec succès.')
        return redirect('admin_examens:concours_liste')


class VueResultatsConcoursBlanc(AdminRequis, View):

    def get(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)

        # Finalisation automatique des tentatives si l'heure de fin est dépassée
        finaliser_tentatives_expirees(concours)

        participants = concours.participants.prefetch_related('tentatives', 'tentatives__epreuve').all()

        # Tri par score total décroissant
        participants_liste = list(participants)
        participants_liste.sort(key=lambda p: p.score_total, reverse=True)

        return render(request, 'examens/admin/concours_resultats.html', {
            'concours': concours,
            'participants': participants_liste,
            'epreuves_concours': concours.concours_epreuves.select_related('epreuve').order_by('ordre'),
        })


class VueSupprimerParticipantConcours(AdminRequis, View):

    def post(self, request, concours_id, participant_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)
        participant = get_object_or_404(ParticipantConcours, id=participant_id, concours=concours)

        participant.delete()
        messages.success(request, f'Le résultat de {participant.nom} a été supprimé avec succès.')
        return redirect('admin_examens:concours_resultats', concours_id=concours.id)


class VueBasculerPublicationClassement(AdminRequis, View):

    def post(self, request, concours_id):
        concours = get_object_or_404(ConcoursBlanc, id=concours_id)
        concours.classement_publie = not concours.classement_publie
        concours.save()

        etat = "publié" if concours.classement_publie else "masqué"
        messages.success(request, f'Le classement est désormais {etat} publiquement.')
        return redirect('admin_examens:concours_resultats', concours_id=concours.id)
