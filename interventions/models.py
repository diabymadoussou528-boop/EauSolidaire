from django.db import models
from pannes.models import Panne
from techniciens.models import Technicien
from stock.models import PieceDetachee


class Intervention(models.Model):
    """Intervention technique de maintenance ou réparation sur une panne."""

    STATUT_CHOICES = [
        ('Affectée', 'Affectée'),
        ('En cours de réparation', 'En cours de réparation'),
        ('Terminée', 'Terminée'),
        ('Clôturée', 'Clôturée'),
    ]

    panne = models.ForeignKey(
        Panne,
        on_delete=models.PROTECT,
        related_name='interventions',
        verbose_name='Panne concernée',
    )
    technicien = models.ForeignKey(
        Technicien,
        on_delete=models.PROTECT,
        related_name='interventions',
        verbose_name='Technicien affecté',
    )
    date_affectation = models.DateTimeField("Date d'affectation", auto_now_add=True)
    date_debut = models.DateTimeField('Date de début', null=True, blank=True)
    date_fin = models.DateTimeField('Date de fin', null=True, blank=True)
    travaux_realises = models.TextField('Travaux réalisés / Compte rendu', blank=True)
    cout_eventuel = models.DecimalField('Coût éventuel (FCFA)', max_digits=12, decimal_places=2, default=0)
    statut = models.CharField('Statut de l’intervention', max_length=50, choices=STATUT_CHOICES, default='Affectée')

    class Meta:
        verbose_name = 'Intervention'
        verbose_name_plural = 'Interventions'
        ordering = ['-date_affectation', '-id']

    def __str__(self):
        return f"Intervention #{self.id} - {self.panne.point_eau.identifiant} ({self.technicien.nom_complet})"


class PieceUtiliseeIntervention(models.Model):
    """Pièces détachées consommées lors d'une intervention."""

    intervention = models.ForeignKey(
        Intervention,
        on_delete=models.CASCADE,
        related_name='pieces_utilisees',
        verbose_name='Intervention',
    )
    piece = models.ForeignKey(
        PieceDetachee,
        on_delete=models.PROTECT,
        related_name='utilisations_intervention',
        verbose_name='Pièce détachée',
    )
    quantite = models.PositiveIntegerField('Quantité utilisée', default=1)

    class Meta:
        verbose_name = 'Pièce utilisée lors d’une intervention'
        verbose_name_plural = 'Pièces utilisées lors des interventions'

    def __str__(self):
        return f"{self.quantite} x {self.piece.nom} (Intervention #{self.intervention.id})"
