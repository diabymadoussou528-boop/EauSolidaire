from django.test import TestCase
from localisation.models import Region, Cercle, Commune, Village
from points_eau.models import PointEau
from pannes.models import Panne
from techniciens.models import Technicien
from .models import Intervention


class InterventionModelTests(TestCase):
    def test_affectation_intervention(self):
        r = Region.objects.create(nom='Sikasso')
        ce = Cercle.objects.create(nom='Kadiolo', region=r)
        c = Commune.objects.create(nom='Kadiolo', cercle=ce)
        v = Village.objects.create(nom='Kadiolo', commune=c)
        pt = PointEau.objects.create(identifiant='FOR-003', nom='Forage solaire', village=v)
        panne = Panne.objects.create(point_eau=pt, description='Pompe arrêtée', niveau_gravite='Critique')
        tech = Technicien.objects.create(nom_complet='Mamadou Traoré')
        inter = Intervention.objects.create(panne=panne, technicien=tech, statut='En cours de réparation')

        self.assertEqual(panne.technicien_nom, 'Mamadou Traoré')
        self.assertEqual(inter.statut, 'En cours de réparation')
