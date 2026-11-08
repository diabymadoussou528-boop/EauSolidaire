from django.test import TestCase, Client
from django.core import mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from .models import Utilisateur


class UtilisateurModelTests(TestCase):
    def test_creation_utilisateur_email(self):
        user = Utilisateur.objects.create_user(
            email='agent@eausolidaire.ml',
            password='PasswordSecurise123!',
            nom_complet='Agent Test',
            role='AGENT_LOCAL',
        )
        self.assertEqual(user.email, 'agent@eausolidaire.ml')
        self.assertTrue(user.check_password('PasswordSecurise123!'))
        self.assertEqual(user.frontend_role_code, 'local')

    def test_creation_superutilisateur(self):
        admin = Utilisateur.objects.create_superuser(
            email='diabymadoussou528@gmail.com',
            password='StrongAdminPassword123!',
            nom_complet='Administrateur Principal',
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)
        self.assertEqual(admin.role, 'ADMIN')
        self.assertEqual(admin.frontend_role_code, 'admin')

    def test_reinitialisation_mot_de_passe_email_et_confirmation(self):
        user = Utilisateur.objects.create_user(
            email='reset@eausolidaire.ml',
            password='AncienPassword123!',
            nom_complet='Utilisateur Reset',
        )
        client = Client()
        res = client.post(
            '/api/auth/password-reset/',
            data={'email': 'reset@eausolidaire.ml'},
            content_type='application/json',
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()['ok'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('EauSolidaire', mail.outbox[0].subject)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        res_confirm = client.post(
            '/api/auth/password-reset/confirm/',
            data={'uid': uid, 'token': token, 'password': 'NouveauPassword456!'},
            content_type='application/json',
        )
        self.assertEqual(res_confirm.status_code, 200)
        self.assertTrue(res_confirm.json()['ok'])
        user.refresh_from_db()
        self.assertTrue(user.check_password('NouveauPassword456!'))
