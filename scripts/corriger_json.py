import os
import json

DOSSIER = 'concours'
VALID_ESCAPES = {'"', '\\', '/', 'b', 'f', 'n', 'r', 't'}
HEX_DIGITS = set('0123456789abcdefABCDEF')


def corriger_chaine_json(texte):
    """Corrige les séquences d'échappement invalides dans une chaîne JSON brute."""
    resultat = []
    in_string = False
    escape = False
    i = 0
    while i < len(texte):
        char = texte[i]

        if not in_string:
            if char == '"':
                in_string = True
            resultat.append(char)
            i += 1
            continue

        # Nous sommes dans une chaîne JSON
        if escape:
            if char == 'u' and i + 4 < len(texte) and all(c in HEX_DIGITS for c in texte[i+1:i+5]):
                resultat.append('\\u')
                resultat.append(texte[i+1:i+5])
                i += 5
            elif char in VALID_ESCAPES:
                resultat.append('\\' + char)
                i += 1
            else:
                resultat.append('\\\\' + char)
                i += 1
            escape = False
            continue

        if char == '\\':
            escape = True
            i += 1
            continue

        resultat.append(char)
        if char == '"':
            in_string = False
        i += 1

    if escape:
        resultat.append('\\\\')

    return ''.join(resultat)


def corriger_fichier(chemin):
    with open(chemin, 'r', encoding='utf-8') as f:
        contenu = f.read()

    if not contenu.strip():
        print(f"  ⚠️ Vide : {chemin}")
        return

    try:
        json.loads(contenu)
        print(f"  ✓ Déjà valide : {chemin}")
        return
    except json.JSONDecodeError:
        pass

    contenu_corrige = corriger_chaine_json(contenu)

    try:
        json.loads(contenu_corrige)
        with open(chemin, 'w', encoding='utf-8') as f:
            f.write(contenu_corrige)
        print(f"  ✅ Corrigé : {chemin}")
    except json.JSONDecodeError as e:
        print(f"  ❌ Impossible de corriger : {chemin} — {e}")


def corriger_dossier(dossier):
    for racine, _, fichiers in os.walk(dossier):
        for fichier in fichiers:
            if fichier.endswith('.json'):
                chemin = os.path.join(racine, fichier)
                corriger_fichier(chemin)


if __name__ == '__main__':
    print("Correction des fichiers JSON...\n")
    corriger_dossier(DOSSIER)
    print("\nTerminé !")
