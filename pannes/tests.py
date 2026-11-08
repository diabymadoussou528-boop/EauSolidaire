from django.test import TestCase
from localisation.models import Region, Cercle, Commune, Village
from points_eau.models import PointEau
from .models import Panne


class PanneModelTests(TestCase):
    def test_declaration_panne(self):
        r = Region.objects.create(nom='Koulikoro')
        ce = Cercle.objects.create(nom='Kati', region=r)
        c = Commune.objects.create(nom='Siby', cercle=ce)
        v = Village.objects.create(nom='Siby', commune=c)
        pt = PointEau.objects.create(identifiant='PUI-002', nom='Puits à grand diamètre', village=v)

        panne = Panne.objects.create(
            point_eau=pt,
            description='Corde et poulie cassées',
            niveau_gravite='Élevée',
            nom_declarant='Resp. Siby',
        )
        self.assertEqual(panne.statut, 'Nouveau signalement')
        self.assertEqual(panne.to_frontend_dict()['pt'], 'PUI-002')
