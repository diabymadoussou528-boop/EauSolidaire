import getpass
from django.core.management.base import BaseCommand, CommandError
from utilisateurs.models import Utilisateur


class Command(BaseCommand):
    help = (
        "Crée ou met à jour de manière interactive et sécurisée le compte administrateur initial "
        "(par défaut : diabymadoussou528@gmail.com) sans jamais coder de mot de passe en dur."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            default='diabymadoussou528@gmail.com',
            help="Adresse e-mail de l'administrateur (défaut: diabymadoussou528@gmail.com)",
        )
        parser.add_argument(
            '--nom',
            default='Administrateur',
            help="Nom complet de l'administrateur",
        )

    def handle(self, *args, **options):
        email = options['email'].strip()
        nom = options['nom'].strip()

        self.stdout.write(self.style.NOTICE(f"Configuration du compte Administrateur : {email}"))
        password = getpass.getpass("Veuillez saisir le mot de passe initial sécurisé : ")
        password_confirm = getpass.getpass("Veuillez confirmer le mot de passe : ")

        if not password or len(password) < 8:
            raise CommandError("Le mot de passe doit contenir au moins 8 caractères.")
        if password != password_confirm:
            raise CommandError("Les mots de passe ne correspondent pas.")

        user, created = Utilisateur.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'nom_complet': nom,
                'role': 'ADMIN',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            },
        )
        if not created:
            user.nom_complet = nom
            user.role = 'ADMIN'
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True

        user.set_password(password)
        user.save()

        action = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(f"Le compte administrateur {email} a été {action} avec succès."))
