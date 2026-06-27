import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from examens.models import Ecole, Filiere, Epreuve, Question, Choix
from django.db import transaction

with transaction.atomic():
    ecole, _ = Ecole.objects.get_or_create(nom='Test Ecole')
    filiere, _ = Filiere.objects.get_or_create(nom='Test Filiere', ecole=ecole)

    epreuve = Epreuve.objects.create(
        filiere=filiere,
        titre='Epreuve de test (automatique)',
        annee=2026,
        mini_cours='Mini cours de test. $x^2$'
    )

    print(f'Créé epreuve id={epreuve.id} titre="{epreuve.titre}"')

    for i in range(1, 4):
        q = Question.objects.create(epreuve=epreuve, texte=f'Texte de la question {i}', ordre=i)
        print(f'  Créée question id={q.id} ordre={q.ordre}')
        for j in range(1, 5):
            Choix.objects.create(question=q, texte=f'Choix {j} pour Q{i}', est_correct=(j==1))
        print('    4 choix créés (1 correct)')

    total_q = epreuve.questions.count()
    total_choices = sum(q.choix.count() for q in epreuve.questions.all())
    print(f'Total questions: {total_q}, total choix: {total_choices}')
