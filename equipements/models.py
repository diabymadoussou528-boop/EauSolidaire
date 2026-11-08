from django.db import models
from points_eau.models import PointEau


class Equipement(models.Model):
    """Équipement installé sur un point d'eau (pompe, panneau solaire, réservoir, etc.)."""

    TYPE_CHOICES = [
        ('Pompe manuelle', 'Pompe manuelle'),
        ('Pompe solaire', 'Pompe solaire'),
        ('Panneau solaire', 'Panneau solaire'),
        ('Château / Réservoir', 'Château / Réservoir'),
        ('Conduite / Robinetterie', 'Conduite / Robinetterie'),
        ('Autre', 'Autre'),
    ]

    ETAT_CHOICES = [
        ('Fonctionnel', 'Fonctionnel'),
        ('Défaillant', 'Défaillant'),
        ('En maintenance', 'En maintenance'),
        ('Hors service', 'Hors service'),
    ]

    point_eau = models.ForeignKey(
        PointEau,
        on_delete=models.CASCADE,
        related_name='equipements',
        verbose_name="Point d'eau associé",
    )
    nom = models.CharField("Nom de l'équipement", max_length=150)
    type_equipement = models.CharField("Type d'équipement", max_length=80, choices=TYPE_CHOICES, default='Pompe manuelle')
    reference = models.CharField('Référence / Numéro de série', max_length=100, unique=True)
    date_installation = models.DateField("Date d'installation", null=True, blank=True)
    etat = models.CharField('État', max_length=50, choices=ETAT_CHOICES, default='Fonctionnel')
    description = models.TextField('Description / Caractéristiques', blank=True)

    class Meta:
        verbose_name = 'Équipement'
        verbose_name_plural = 'Équipements'
        ordering = ['point_eau__identifiant', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.reference}) - {self.point_eau.identifiant}"

    def to_frontend_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'type': self.type_equipement,
            'ref': self.reference,
            'pt': self.point_eau.identifiant,
            'etat': self.etat,
            'date_installation': self.date_installation.isoformat() if self.date_installation else None,
            'description': self.description,
        }
