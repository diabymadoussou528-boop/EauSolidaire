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

    def test_inscription_connexion_et_otp_six_chiffres(self):
        client = Client()
        res_reg = client.post(
            '/api/auth/register/',
            data={
                'role': 'local',
                'nom': 'Awa Diallo',
                'email': 'awa@mail.ml',
                'tel': '+223 70 00 00 00',
                'npw': 'PasswordFort123!',
                'vil': 'Sadiola',
            },
            content_type='application/json',
        )
        self.assertEqual(res_reg.status_code, 200)
        self.assertTrue(res_reg.json()['ok'])

        # Connexion par téléphone avec vérification du rôle
        res_login = client.post(
            '/api/auth/login/',
            data={'ident': '+22370000000', 'mdp': 'PasswordFort123!', 'role': 'local'},
            content_type='application/json',
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertTrue(res_login.json()['ok'])
        self.assertEqual(res_login.json()['user']['nom'], 'Awa Diallo')

        # Réinitialisation par code OTP à 6 chiffres
        res_otp = client.post(
            '/api/auth/password-reset/',
            data={'email': 'awa@mail.ml', 'mode': 'otp', 'code': '572364'},
            content_type='application/json',
        )
        self.assertEqual(res_otp.status_code, 200)
        self.assertEqual(res_otp.json()['code'], '572364')

        res_confirm_otp = client.post(
            '/api/auth/password-reset/confirm/',
            data={'email': 'awa@mail.ml', 'code': '572364', 'password': 'NouveauMotDePasse99!'},
            content_type='application/json',
        )
        self.assertEqual(res_confirm_otp.status_code, 200)
        self.assertTrue(res_confirm_otp.json()['ok'])
        u = Utilisateur.objects.get(email='awa@mail.ml')
        self.assertTrue(u.check_password('NouveauMotDePasse99!'))

    def test_isolation_notifications_par_compte_et_acces_admin(self):
        client_a = Client()
        client_b = Client()
        client_admin = Client()

        # Inscription Compte A (Responsable local 1)
        client_a.post(
            '/api/auth/register/',
            data={
                'role': 'local',
                'nom': 'Keita Un',
                'email': 'keita1@mail.ml',
                'tel': '+223 71 11 11 11',
                'npw': 'PasswordFort123!',
                'vil': 'Sadiola',
            },
            content_type='application/json',
        )
        # Inscription Compte B (Responsable local 2)
        client_b.post(
            '/api/auth/register/',
            data={
                'role': 'local',
                'nom': 'Diallo Deux',
                'email': 'diallo2@mail.ml',
                'tel': '+223 72 22 22 22',
                'npw': 'PasswordFort123!',
                'vil': 'Siby',
            },
            content_type='application/json',
        )

        # Connexion des 3 comptes
        client_a.post(
            '/api/auth/login/',
            data={'ident': 'keita1@mail.ml', 'mdp': 'PasswordFort123!', 'role': 'local'},
            content_type='application/json',
        )
        client_b.post(
            '/api/auth/login/',
            data={'ident': 'diallo2@mail.ml', 'mdp': 'PasswordFort123!', 'role': 'local'},
            content_type='application/json',
        )
        client_admin.post(
            '/api/auth/login/',
            data={'ident': 'diabymadoussou528@gmail.com', 'mdp': 'Admin1234', 'role': 'admin'},
            content_type='application/json',
        )

        # Compte A déclare une panne sur FOR-001
        client_a.post(
            '/api/pannes/add/',
            data={'pt': 'FOR-001', 'd': 'Fuite pompe manuelle', 'p': 'Élevée'},
            content_type='application/json',
        )

        notifs_a = client_a.get('/api/state/').json()['D']['notifs']
        notifs_b = client_b.get('/api/state/').json()['D']['notifs']
        notifs_admin = client_admin.get('/api/state/').json()['D']['notifs']

        # Compte A voit uniquement ses notifications personnelles
        self.assertIn('Signalement enregistré : FOR-001', notifs_a)
        self.assertNotIn('Bienvenue Diallo Deux (Responsable local)', notifs_a)
        self.assertNotIn('Stock faible : Clapet de pompe manuelle', notifs_a)

        # Compte B ne voit PAS les notifications de Compte A ni celles de la plateforme globale
        self.assertNotIn('Signalement enregistré : FOR-001', notifs_b)
        self.assertNotIn('Nouveau signalement : FOR-001', notifs_b)
        self.assertNotIn('Bienvenue Keita Un (Responsable local)', notifs_b)
        self.assertIn('Bienvenue Diallo Deux (Responsable local)', notifs_b)

        # L'administrateur voit toutes les notifications globales de la plateforme
        self.assertIn('Nouveau signalement : FOR-001', notifs_admin)
        self.assertIn('Nouveau compte : Keita Un (Responsable local)', notifs_admin)
        self.assertIn('Nouveau compte : Diallo Deux (Responsable local)', notifs_admin)


