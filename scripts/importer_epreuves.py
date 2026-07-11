import os
import sys
import django
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from examens.models import Ecole, Filiere, Epreuve, Question, Choix

# Commandes LaTeX connues — triées par longueur au moment du remplacement
LATEX_COMMANDS = [
    'right', 'left', 'dfrac', 'frac', 'sqrt', 'sum', 'int',
    'infty', 'mathbb', 'mathcal', 'cdot', 'times', 'leq', 'geq',
    'neq', 'ne', 'ge', 'le', 'approx', 'equiv', 'forall', 'exists',
    'in', 'notin', 'to',
    'subset', 'supset', 'cup', 'cap', 'emptyset', 'alpha', 'beta',
    'gamma', 'delta', 'epsilon', 'theta', 'lambda', 'mu', 'pi',
    'sigma', 'omega', 'partial', 'nabla', 'pm', 'mp', 'div',
    'overline', 'underline', 'hat', 'vec', 'bar', 'dot', 'ddot',
    'lim', 'max', 'min', 'log', 'ln', 'sin', 'cos', 'tan',
    'arcsin', 'arccos', 'arctan', 'exp', 'begin', 'end',
    'text', 'mathrm', 'textbf', 'textit', 'limits',
    'underbrace', 'overbrace', 'binom', 'pmatrix', 'bmatrix',
    'vmatrix', 'matrix', 'quad', 'qquad', 'iff', 'implies',
    'rightarrow', 'leftarrow', 'Rightarrow', 'Leftarrow',
    'sim', 'cong', 'perp', 'parallel', 'ldots', 'cdots',
    'vdots', 'ddots', 'not', 'Big', 'Bigg', 'big', 'bigg',
    'sinh', 'cosh', 'tanh', 'mapsto', 'hspace', 'vspace',
    'Re', 'Im', 'aleph', 'prod', 'bigl', 'bigr', 'Bigl', 'Bigr',
]

# Symboles LaTeX qui posent problème lorsqu'ils sont précédés d'un seul backslash
LATEX_SYMBOLS = ['{', '}', ';', ',', '!', ':', '|', '[', ']', '(', ')', '%']


def nettoyer_latex_brut(texte_brut):
    """
    Nettoie le contenu BRUT d'un fichier JSON avant `json.loads`.
    Remplace les occurrences comme "\\neq", "\\times", "\\right"
    par des séquences correctement échappées ("\\\\neq"...),
    afin que `json.loads` ne transforme pas `\n`, `\t`, `\r`, etc.
    """
    if not texte_brut:
        return texte_brut

    # 1) Commandes nommées : remplacer \cmd par \\cmd lorsque nécessaire
    for cmd in sorted(LATEX_COMMANDS, key=len, reverse=True):
        texte_brut = re.sub(
            r'(?<!\\)\\(' + re.escape(cmd) + r')(?![a-zA-Z])',
            r'\\\\\1',
            texte_brut,
        )

    # 2) Symboles particuliers: \{, \}, \;, \, ...
    for symbole in LATEX_SYMBOLS:
        texte_brut = re.sub(
            r'(?<!\\)\\(?=' + re.escape(symbole) + r')',
            r'\\\\',
            texte_brut,
        )

    return texte_brut

def importer_fichier(fichier_json):
    with open(fichier_json, 'r', encoding='utf-8') as f:
        contenu = f.read()

    # Ignore les fichiers vides
    if not contenu.strip():
        print(f"    ⚠ Fichier vide — ignoré")
        return

    # Étape cruciale : nettoyer le LaTeX AVANT json.loads
    contenu_corrige = nettoyer_latex_brut(contenu)
    try:
        donnees = json.loads(contenu_corrige)
    except json.JSONDecodeError as e:
        # Affiche un contexte utile pour debug
        pos = e.pos
        print(f"    ❌ JSON invalide après nettoyage : {e}")
        print(f"    Contexte : ...{contenu_corrige[max(0, pos-40):pos+40]}...")
        raise

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
                # Met à jour le mini_cours si déjà existant
                if item_epreuve.get('mini_cours'):
                    epreuve.mini_cours = item_epreuve.get('mini_cours', '')
                    epreuve.save()
                print(f"    ⚠ Déjà existante : {epreuve.titre} {epreuve.annee} — mise à jour mini cours")
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