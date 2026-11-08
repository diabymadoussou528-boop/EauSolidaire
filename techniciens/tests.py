from django.test import TestCase
from .models import Technicien


class TechnicienModelTests(TestCase):
    def test_creation_technicien(self):
        tech = Technicien.objects.create(
            nom_complet='Mamadou Traoré',
            specialite='Systèmes solaires et pompes manuelles',
            disponible=True,
        )
        self.assertTrue(tech.disponible)
        self.assertIn('Mamadou Traoré', str(tech))
