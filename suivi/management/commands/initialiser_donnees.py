from django.core.management.base import BaseCommand
from suivi.views import initialiser_donnees_base_si_vide


class Command(BaseCommand):
    help = "Initialise la base de données MySQL avec les régions, villages, points d'eau, équipements, techniciens, pannes et stocks d'EauSolidaire."

    def handle(self, *args, **options):
        initialiser_donnees_base_si_vide()
        self.stdout.write(self.style.SUCCESS("Les données initiales d'EauSolidaire ont été enregistrées dans MySQL avec succès."))
