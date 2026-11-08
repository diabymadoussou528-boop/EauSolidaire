from django.test import TestCase
from .models import Region, Cercle, Commune, Village


class LocalisationHierarchyTests(TestCase):
    def test_hierarchie_complete(self):
        region = Region.objects.create(nom='Koulikoro')
        cercle = Cercle.objects.create(nom='Kati', region=region)
        commune = Commune.objects.create(nom='Siby', cercle=cercle)
        village = Village.objects.create(nom='Siby', commune=commune)

        self.assertEqual(village.region.nom, 'Koulikoro')
        self.assertEqual(village.cercle.nom, 'Kati')
        self.assertEqual(village.commune.nom, 'Siby')
        self.assertEqual(village.to_frontend_dict()['r'], 'Koulikoro')
