from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UtilisateurManager(BaseUserManager):
    """Gestionnaire personnalisé permettant la connexion par adresse e-mail."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse e-mail est obligatoire.")
        email = self.normalize_email(email)
        if not extra_fields.get('username'):
            extra_fields['username'] = email
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')
        if not password:
            raise ValueError('Un mot de passe sécurisé est obligatoire pour le superutilisateur.')

        return self.create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé d'EauSolidaire basé sur AbstractUser."""

    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('RESPONSABLE', 'Responsable'),
        ('TECHNICIEN', 'Technicien'),
        ('AGENT_LOCAL', 'Agent local'),
    ]

    email = models.EmailField('Adresse e-mail', unique=True)
    nom_complet = models.CharField('Nom complet', max_length=150, blank=True)
    telephone = models.CharField('Téléphone', max_length=30, blank=True)
    role = models.CharField('Rôle', max_length=20, choices=ROLE_CHOICES, default='AGENT_LOCAL')
    village = models.ForeignKey(
        'localisation.Village',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='utilisateurs',
        verbose_name='Village rattaché',
    )
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = UtilisateurManager()

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['email']

    def __str__(self):
        return f"{self.get_display_name()} ({self.get_role_display()})"

    def get_display_name(self):
        if self.nom_complet:
            return self.nom_complet
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username or self.email

    @property
    def frontend_role_code(self):
        """Retourne le code de rôle attendu par l'interface existante ('admin', 'local', 'tech')."""
        if self.is_superuser or self.role in ('ADMIN', 'RESPONSABLE'):
            return 'admin'
        if self.role == 'TECHNICIEN':
            return 'tech'
        return 'local'


class Notification(models.Model):
    """Notifications système affichées dans la cloche de l'interface."""

    message = models.CharField('Message', max_length=255)
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Destinataire (optionnel)',
    )
    lue = models.BooleanField('Lue', default=False)
    date_creation = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-date_creation']

    def __str__(self):
        return self.message


class MessageContact(models.Model):
    """Messages envoyés depuis le formulaire de contact public."""

    SUJET_CHOICES = [
        ('Information', 'Information'),
        ('Signaler une panne', 'Signaler une panne'),
        ('Partenariat', 'Partenariat'),
        ('Autre', 'Autre'),
    ]

    sujet = models.CharField('Sujet', max_length=100, choices=SUJET_CHOICES, default='Information')
    nom_complet = models.CharField('Nom complet', max_length=150)
    email = models.EmailField('Adresse e-mail')
    message = models.TextField('Message', max_length=500)
    traite = models.BooleanField('Traité', default=False)
    date_envoi = models.DateTimeField("Date d'envoi", auto_now_add=True)

    class Meta:
        verbose_name = 'Message de contact'
        verbose_name_plural = 'Messages de contact'
        ordering = ['-date_envoi']

    def __str__(self):
        return f"{self.sujet} - {self.nom_complet} ({self.email})"

    def to_frontend_dict(self):
        return {
            'id': self.id,
            'sj': self.sujet,
            'nom': self.nom_complet,
            'email': self.email,
            'msg': self.message,
            'traite': self.traite,
            'date': self.date_envoi.strftime('%d/%m/%Y %H:%M') if self.date_envoi else '',
        }
