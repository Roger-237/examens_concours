import os
import sys
import django
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from examens.models import Ecole, Filiere, Epreuve, Question, Choix


def importer_fichier(fichier_json):
    with open(fichier_json, 'r', encoding='utf-8') as f:
        donnees = json.load(f)

    for item in donnees:
        ecole, _ = Ecole.objects.get_or_create(nom=item['ecole'])
        print(f"\n École : {ecole.nom}")

        nom_filiere = item.get('filiere', 'Générale')
        filiere, _ = Filiere.objects.get_or_create(nom=nom_filiere, ecole=ecole)
        print(f"  Filière : {filiere.nom}")

        for item_epreuve in item['epreuves']:
            epreuve, creee = Epreuve.objects.get_or_create(
                filiere=filiere,
                titre=item_epreuve['titre'],
                annee=item_epreuve['annee'],
                defaults={'mini_cours': item_epreuve.get('mini_cours', '')}
            )

            if not creee:
                print(f"    ⚠ Déjà existante : {epreuve.titre} {epreuve.annee} — ignorée")
                continue

            print(f"    ✓ Épreuve créée : {epreuve.titre} {epreuve.annee}")

            for q_data in item_epreuve['questions']:
                question = Question.objects.create(
                    epreuve=epreuve,
                    texte=q_data['texte'],
                    ordre=q_data['ordre'],
                )
                for c_data in q_data['choix']:
                    Choix.objects.create(
                        question=question,
                        texte=c_data['texte'],
                        est_correct=c_data.get('est_correct', False),
                    )
                print(f"      Q{question.ordre} ✓")


def importer_dossier(dossier):
    """Parcourt récursivement le dossier et importe tous les fichiers JSON"""
    total = 0
    erreurs = []

    for racine, sous_dossiers, fichiers in os.walk(dossier):
        for fichier in fichiers:
            if fichier.endswith('.json'):
                chemin = os.path.join(racine, fichier)
                print(f"\n{'='*50}")
                print(f"Traitement : {chemin}")
                print('='*50)
                try:
                    importer_fichier(chemin)
                    total += 1
                except Exception as e:
                    print(f"    ❌ Erreur : {e}")
                    erreurs.append((chemin, str(e)))

    print(f"\n✅ Import terminé — {total} fichier(s) traité(s) !")
    if erreurs:
        print(f"\n⚠ {len(erreurs)} fichier(s) en erreur :")
        for chemin, err in erreurs:
            print(f"  - {chemin} : {err}")


if __name__ == '__main__':
    dossier = sys.argv[1] if len(sys.argv) > 1 else 'concours'
    importer_dossier(dossier)