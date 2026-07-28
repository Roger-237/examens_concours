import json
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.db import transaction, IntegrityError
from django.db.models import Count
from django.http import JsonResponse
from examens.models import (
    ConcoursBlanc, ConcoursBlancEpreuve, ParticipantConcours,
    TentativeConcoursParticipant, ReponseConcoursParticipant,
    Question, Choix
)
from examens.formulaires import FormulaireInscriptionConcours
from examens.vues_admin import finaliser_tentatives_expirees


# ─────────────────────────────────────────
#  ACCUEIL / DÉTAILS CONCOURS BLANC (PUBLIC)
# ─────────────────────────────────────────
class VueAccueilConcours(View):

    def get(self, request):
        concours = ConcoursBlanc.objects.filter(
            statut='publie',
            heure_fin__gt=timezone.now()
        ).select_related('ecole').first()

        classement_concours = ConcoursBlanc.objects.filter(
            classement_publie=True,
            statut__in=['publie', 'termine']
        ).annotate(participants_count=Count('participants')).filter(participants_count__gt=0)
        classement_concours = classement_concours.select_related('ecole').order_by('-heure_fin').first()

        token = request.GET.get('token') or request.COOKIES.get('concours_token')
        participant = None
        if token:
            try:
                participant = ParticipantConcours.objects.filter(token=token).first()
            except Exception:
                participant = None

        formulaire = FormulaireInscriptionConcours()

        return render(request, 'examens/concours/accueil.html', {
            'concours': concours,
            'classement_concours': classement_concours,
            'participant': participant,
            'formulaire': formulaire,
            'places_restantes': concours.places_restantes() if concours else 0,
        })


# ─────────────────────────────────────────
#  INSCRIPTION PARTICIPANT (SANS COMPTE)
# ─────────────────────────────────────────
class VueInscriptionConcours(View):

    def post(self, request):
        concours = ConcoursBlanc.objects.filter(statut='publie').first()

        if not concours or timezone.now() < concours.heure_debut:
            messages.error(request, "Les inscriptions pour ce concours ne sont pas ouvertes actuellement.")
            return redirect('concours:accueil')

        if timezone.now() > concours.heure_fin:
            messages.error(request, "Le concours blanc est terminé, les inscriptions sont closes.")
            return redirect('concours:accueil')

        formulaire = FormulaireInscriptionConcours(request.POST)
        if not formulaire.is_valid():
            messages.error(request, "Nom invalide. Veuillez entrer un nom complet valide.")
            return redirect('concours:accueil')

        nom_saisi = formulaire.cleaned_data['nom'].strip()

        try:
            with transaction.atomic():
                concours_locked = ConcoursBlanc.objects.select_for_update().get(id=concours.id)

                if concours_locked.participants.count() >= concours_locked.nb_places_max:
                    messages.error(request, "Inscriptions closes : le nombre maximum de places a été atteint.")
                    return redirect('concours:accueil')

                if ParticipantConcours.objects.filter(concours=concours_locked, nom__iexact=nom_saisi).exists():
                    messages.error(request, f"Le nom \"{nom_saisi}\" est déjà inscrit à ce concours Blanc. Veuillez ajouter votre prénom ou un identifiant.")
                    return redirect('concours:accueil')

                participant = ParticipantConcours.objects.create(
                    concours=concours_locked,
                    nom=nom_saisi,
                )
        except IntegrityError:
            messages.error(request, f"Le nom \"{nom_saisi}\" est déjà inscrit à ce concours Blanc.")
            return redirect('concours:accueil')

        temps_restant = int((concours.heure_fin - timezone.now()).total_seconds())

        response = redirect('concours:passer_token', token=participant.token)
        if temps_restant > 0:
            response.set_cookie('concours_token', str(participant.token), max_age=temps_restant, httponly=True)

        return response


# ─────────────────────────────────────────
#  PASSER / REPRENDRE LE CONCOURS
# ─────────────────────────────────────────
class VuePasserConcours(View):

    def get_participant(self, request, token=None):
        token_uuid = token or request.COOKIES.get('concours_token')
        if not token_uuid:
            return None
        try:
            return ParticipantConcours.objects.select_related('concours').filter(token=token_uuid).first()
        except Exception:
            return None

    def get(self, request, token=None):
        participant = self.get_participant(request, token)
        if not participant:
            messages.error(request, "Session non trouvée. Veuillez vous inscrire ou utiliser votre lien direct de secours.")
            return redirect('concours:accueil')

        concours = participant.concours

        # Bloqué net si l'heure de fin est dépassée
        if timezone.now() > concours.heure_fin:
            finaliser_tentatives_expirees(concours)
            return redirect('concours:fin_token', token=participant.token)

        concours_epreuves = list(concours.concours_epreuves.select_related('epreuve').order_by('ordre'))
        if not concours_epreuves:
            messages.error(request, "Ce concours ne contient aucune épreuve.")
            return redirect('concours:accueil')

        # Préparer toutes les tentatives et leurs données
        epreuves_data = []
        epreuve_active = None
        epreuve_active_id = request.GET.get('epreuve_id')
        total_questions_global = 0
        total_reponses_global = 0

        for ce in concours_epreuves:
            tentative, _ = TentativeConcoursParticipant.objects.get_or_create(
                participant=participant,
                epreuve=ce.epreuve,
            )
            
            # Récupérer toutes les questions de l'épreuve
            questions = list(tentative.epreuve.questions.order_by('ordre').prefetch_related('choix'))
            total_questions_global += len(questions)
            
            # Récupérer les réponses déjà données
            reponses_dict = {
                r.question_id: r.choix_id 
                for r in tentative.reponses.all()
            }
            nb_reponses_epreuve = len([r for r in reponses_dict.values() if r is not None])
            total_reponses_global += nb_reponses_epreuve
            
            # Déterminer la question à afficher (première non répondue ou première)
            question_active = None
            for q in questions:
                if q.id not in reponses_dict or reponses_dict[q.id] is None:
                    question_active = q
                    break
            if question_active is None:
                question_active = questions[0] if questions else None
            
            epreuves_data.append({
                'concours_epreuve': ce,
                'epreuve': ce.epreuve,
                'tentative': tentative,
                'questions': questions,
                'reponses': reponses_dict,
                'reponses_json': mark_safe(json.dumps(reponses_dict)),
                'nb_reponses': nb_reponses_epreuve,
                'total_questions': len(questions),
                'question_active': question_active,
            })
            
            # Sélectionner l'épreuve active
            if epreuve_active_id:
                if str(ce.epreuve.id) == epreuve_active_id:
                    epreuve_active = epreuves_data[-1]
            else:
                if epreuve_active is None:
                    epreuve_active = epreuves_data[-1]

        if not epreuve_active:
            epreuve_active = epreuves_data[0]

        temps_restant = int((concours.heure_fin - timezone.now()).total_seconds())

        response = render(request, 'examens/concours/passer.html', {
            'participant': participant,
            'concours': concours,
            'epreuves_data': epreuves_data,
            'epreuve_active': epreuve_active,
            'total_questions_global': total_questions_global,
            'total_reponses_global': total_reponses_global,
            'temps_restant': max(0, temps_restant),
        })

        if temps_restant > 0:
            response.set_cookie('concours_token', str(participant.token), max_age=temps_restant, httponly=True)

        return response

    def post(self, request, token=None):
        participant = self.get_participant(request, token)
        if not participant:
            return JsonResponse({'error': 'Participant non trouvé'}, status=404)

        concours = participant.concours

        if timezone.now() > concours.heure_fin:
            finaliser_tentatives_expirees(concours)
            return JsonResponse({'redirect': f"/concours-blanc/fin/{participant.token}/"}, status=403)

        action = request.POST.get('action')

        if action == 'marquer_revue':
            # Marquer l'épreuve comme revue (sans verrouiller)
            tentative_id = request.POST.get('tentative_id')
            tentative = get_object_or_404(
                TentativeConcoursParticipant,
                id=tentative_id,
                participant=participant,
            )
            tentative.revue = True
            tentative.save()
            return JsonResponse({'success': True})

        if action == 'terminer':
            # Finalisation manuelle par le participant
            return self.terminer_participation(request, participant, concours)
        
        # Enregistrement d'une réponse
        question_id = request.POST.get('question_id')
        choix_id = request.POST.get('choix_id')
        tentative_id = request.POST.get('tentative_id')

        tentative = get_object_or_404(
            TentativeConcoursParticipant,
            id=tentative_id,
            participant=participant,
        )

        question = get_object_or_404(Question, id=question_id, epreuve=tentative.epreuve)
        choix = None
        if choix_id:
            choix = Choix.objects.filter(id=choix_id, question=question).first()

        # Enregistrement immédiat par question
        ReponseConcoursParticipant.objects.update_or_create(
            tentative=tentative,
            question=question,
            defaults={'choix': choix}
        )

        return JsonResponse({'success': True})
    
    def terminer_participation(self, request, participant, concours):
        """Finalise toutes les tentatives du participant et calcule les scores"""
        try:
            with transaction.atomic():
                for tentative in participant.tentatives.all():
                    # Calculer le score de cette tentative
                    reponses = {r.question_id: r.choix for r in tentative.reponses.select_related('choix').all()}
                    score = 0
                    for q in tentative.epreuve.questions.all():
                        c = reponses.get(q.id)
                        if c:
                            if c.est_correct:
                                score += 1
                            else:
                                score -= 1
                    tentative.score = score
                    tentative.terminee = True
                    tentative.date_fin = timezone.now()
                    tentative.save()
        
            return JsonResponse({'success': True, 'redirect': f"/concours-blanc/fin/{participant.token}/"})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


# ─────────────────────────────────────────
#  FIN DU CONCOURS (SCORE MASQUÉ)
# ─────────────────────────────────────────
class VueFinConcours(View):

    def get(self, request, token=None):
        token_uuid = token or request.COOKIES.get('concours_token')
        participant = None
        if token_uuid:
            participant = ParticipantConcours.objects.filter(token=token_uuid).first()

        if participant:
            finaliser_tentatives_expirees(participant.concours)

        return render(request, 'examens/concours/fin.html', {
            'participant': participant,
        })


# ─────────────────────────────────────────
#  CLASSEMENT PUBLIC (SI PUBLIÉ PAR L'ADMIN)
# ─────────────────────────────────────────
class VueClassementConcours(View):

    def get(self, request, concours_id=None):
        classements = ConcoursBlanc.objects.filter(
            classement_publie=True,
            statut__in=['publie', 'termine']
        ).annotate(participants_count=Count('participants')).filter(participants_count__gt=0)
        classements = classements.select_related('ecole').order_by('-heure_fin')

        if concours_id:
            concours = get_object_or_404(classements, id=concours_id)
        else:
            if not classements.exists():
                messages.info(request, "Aucun concours blanc à afficher.")
                return redirect('accueil')
            if classements.count() > 1:
                return render(request, 'examens/concours/classement_liste.html', {
                    'classements': classements,
                })
            concours = classements.first()

        if not concours.classement_publie:
            return render(request, 'examens/concours/classement_masque.html', {
                'concours': concours,
            })

        finaliser_tentatives_expirees(concours)

        participants = list(concours.participants.prefetch_related('tentatives', 'tentatives__epreuve').all())
        participants.sort(key=lambda p: p.score_total, reverse=True)

        epreuves_concours = concours.concours_epreuves.select_related('epreuve').order_by('ordre')

        return render(request, 'examens/concours/classement.html', {
            'concours': concours,
            'participants': participants,
            'epreuves_concours': epreuves_concours,
        })
