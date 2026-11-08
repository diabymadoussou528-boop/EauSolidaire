from django.conf import settings
from django.db import models
from localisation.models import Region


class Technicien(models.Model):
    """Informations personnelles, professionnelles, compétences et disponibilité d'un technicien."""

    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profil_technicien',
        verbose_name='Compte utilisateur lié',
    )
    nom_complet = models.CharField('Nom complet', max_length=150, unique=True)
    telephone = models.CharField('Téléphone', max_length=30, blank=True)
    email = models.EmailField('Adresse e-mail professionnelle', blank=True)
    specialite = models.CharField(
        'Spécialité / Compétences',
        max_length=200,
        default='Hydraulique villageoise, pompes manuelles et solaires',
    )
    region_affectation = models.ForeignKey(
        Region,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='techniciens',
        verbose_name="Région d'affectation",
    )
    disponible = models.BooleanField('Disponible', default=True)
    date_embauche = models.DateField("Date d'entrée en fonction", null=True, blank=True)

    class Meta:
        verbose_name = 'Technicien'
        verbose_name_plural = 'Techniciens'
        ordering = ['nom_complet']

    def __str__(self):
        statut = 'Disponible' if self.disponible else 'Indisponible'
        return f"{self.nom_complet} ({statut})"
