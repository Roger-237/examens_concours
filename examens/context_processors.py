from django.db.models import Count
from django.utils import timezone
from .models import ConcoursBlanc


def concours_blanc_actif(request):
    """
    Context processor renvoyant le concours blanc actif en statut 'publie'
    dont l'heure de fin n'est pas encore dépassée, ainsi que les classements
    publiés les plus récents.
    """
    try:
        concours = ConcoursBlanc.objects.filter(
            statut='publie',
            heure_fin__gt=timezone.now()
        ).select_related('ecole').first()
    except Exception:
        concours = None

    try:
        classement_concours = ConcoursBlanc.objects.filter(
            classement_publie=True,
            statut__in=['publie', 'termine']
        ).annotate(participants_count=Count('participants')).filter(participants_count__gt=0)
        classement_concours = classement_concours.select_related('ecole').order_by('-heure_fin')
    except Exception:
        classement_concours = []

    return {
        'concours_blanc_actif': concours,
        'classement_concours_pub': classement_concours,
    }
