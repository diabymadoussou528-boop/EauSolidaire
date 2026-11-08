from django.test import TestCase
from .models import RapportActivite


class RapportModelTests(TestCase):
    def test_creation_rapport(self):
        rapport = RapportActivite.objects.create(
            titre='Rapport mensuel hydraulique',
            total_points_eau=7,
            points_fonctionnels=4,
            taux_disponibilite=57.1,
        )
        self.assertEqual(rapport.total_points_eau, 7)
