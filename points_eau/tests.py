from django.test import TestCase
from localisation.models import Region, Cercle, Commune, Village
from .models import PointEau


class PointEauModelTests(TestCase):
    def setUp(self):
        r = Region.objects.create(nom='Kayes')
        ce = Cercle.objects.create(nom='Kéniéba', region=r)
        c = Commune.objects.create(nom='Sadiola', cercle=ce)
        self.village = Village.objects.create(nom='Sadiola', commune=c)

    def test_creation_point_eau(self):
        pt = PointEau.objects.create(
            identifiant='FOR-001',
            nom='Forage à pompe manuelle du marché',
            type_point='Forage',
            village=self.village,
            latitude=13.85,
            longitude=-11.7,
            etat_fonctionnement='Fonctionnel',
        )
        self.assertEqual(pt.village.nom, 'Sadiola')
        self.assertEqual(pt.to_frontend_dict()['ref'], 'FOR-001')
