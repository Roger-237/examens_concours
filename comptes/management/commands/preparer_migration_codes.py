import csv
import random
from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from comptes.models import Eleve, MigrationCodeAcces


def generer_code_complexe():
    """Génère un code complexe de 10 caractères (2 maj + 2 min + 2 chiffres + 2 spéciaux + 2 mixtes)."""
    majuscules = get_random_string(2, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZ')
    minuscules = get_random_string(2, allowed_chars='abcdefghjkmnpqrstuvwxyz')
    chiffres   = get_random_string(2, allowed_chars='23456789')
    speciaux   = get_random_string(2, allowed_chars='#@$*!?')
    reste      = get_random_string(2, allowed_chars='ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789')
    code = list(majuscules + minuscules + chiffres + speciaux + reste)
    random.shuffle(code)
    return ''.join(code)


class Command(BaseCommand):
    help = "Prépare les nouveaux codes d'accès complexes (sans les activer) et exporte une liste de secours CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            '--fichier',
            default='migration_codes.csv',
            help="Nom du fichier CSV de sortie (défaut: migration_codes.csv)"
        )

    def handle(self, *args, **options):
        # Récupérer uniquement les élèves sans migration déjà préparée
        eleves = Eleve.objects.filter(migration_code__isnull=True)
        total = eleves.count()

        if total == 0:
            self.stdout.write(self.style.WARNING(
                "Aucun élève à migrer — tous les codes sont déjà préparés."
            ))
            return

        lignes = []

        for eleve in eleves:
            # Générer un code unique non utilisé en base
            nouveau_code = generer_code_complexe()
            tentatives = 0
            while Eleve.objects.filter(code_acces=nouveau_code).exists():
                nouveau_code = generer_code_complexe()
                tentatives += 1
                if tentatives > 100:
                    self.stderr.write(f"Impossible de générer un code unique pour {eleve.nom_complet}")
                    break

            MigrationCodeAcces.objects.create(
                eleve=eleve,
                ancien_code=eleve.code_acces,
                nouveau_code=nouveau_code,
            )
            lignes.append([eleve.nom_complet, eleve.code_acces, nouveau_code])
            self.stdout.write(f"  Préparé : {eleve.nom_complet}")

        # Export CSV de secours
        fichier = options['fichier']
        with open(fichier, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Nom complet', 'Ancien code', 'Nouveau code'])
            writer.writerows(lignes)

        self.stdout.write(self.style.SUCCESS(
            f"\n✅ {len(lignes)} code(s) préparé(s). Liste de secours exportée dans : {fichier}"
        ))
        self.stdout.write(self.style.WARNING(
            "⚠️  Gardez ce fichier en lieu sûr — ne le commitez PAS dans Git."
        ))
