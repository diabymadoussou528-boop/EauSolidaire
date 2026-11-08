from django.test import TestCase, Client
from localisation.models import Region, Cercle, Commune, Village
from points_eau.models import PointEau
from utilisateurs.models import Utilisateur
from .models import Equipement


class EquipementModelTests(TestCase):
    def test_creation_equipement(self):
        r = Region.objects.create(nom='Sikasso')
        ce = Cercle.objects.create(nom='Kadiolo', region=r)
        c = Commune.objects.create(nom='Kadiolo', cercle=ce)
        v = Village.objects.create(nom='Kadiolo', commune=c)
        pt = PointEau.objects.create(identifiant='FOR-003', nom='Forage solaire', village=v)
        eq = Equipement.objects.create(
            point_eau=pt,
            nom='Pompe immergée Grundfos',
            type_equipement='Pompe solaire',
            reference='EQ-KAD-01',
        )
        self.assertEqual(eq.point_eau.identifiant, 'FOR-003')

    def test_api_crud_equipement(self):
        r = Region.objects.create(nom='Koulikoro')
        ce = Cercle.objects.create(nom='Kati', region=r)
        c = Commune.objects.create(nom='Siby', cercle=ce)
        v = Village.objects.create(nom='Siby', commune=c)
        pt = PointEau.objects.create(identifiant='FOR-001', nom='Forage central', village=v)
        admin = Utilisateur.objects.create_superuser(
            email='admin@eausolidaire.ml',
            password='AdminPassword123!',
            nom_complet='Admin Test',
        )
        client = Client()
        client.force_login(admin)

        res_add = client.post(
            '/api/equipements/add/',
            data={'pt': 'FOR-001', 'nom': 'Pompe India Mark II', 'ref': 'EQ-TEST-01', 'type': 'Pompe manuelle'},
            content_type='application/json',
        )
        self.assertEqual(res_add.status_code, 200)
        self.assertTrue(res_add.json()['ok'])

        res_etat = client.post(
            '/api/equipements/etat/',
            data={'ref': 'EQ-TEST-01', 'etat': 'En maintenance'},
            content_type='application/json',
        )
        self.assertEqual(res_etat.status_code, 200)
        self.assertEqual(Equipement.objects.get(reference='EQ-TEST-01').etat, 'En maintenance')

        res_del = client.post(
            '/api/equipements/delete/',
            data={'ref': 'EQ-TEST-01'},
            content_type='application/json',
        )
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(Equipement.objects.filter(reference='EQ-TEST-01').exists())
