from django.test import TestCase
from django.urls import reverse


class SuiviViewsTests(TestCase):
    def test_page_accueil_charge_interface_intacte(self):
        response = self.client.get(reverse('suivi:accueil'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EauSolidaire')

    def test_api_state_initialise_donnees(self):
        response = self.client.get(reverse('suivi:api_state'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertGreaterEqual(len(data['D']['pts']), 7)
        self.assertGreaterEqual(len(data['D']['villages']), 6)
