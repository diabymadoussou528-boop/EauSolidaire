from django.conf import settings
from django.db import models
from points_eau.models import PointEau
from equipements.models import Equipement


class Panne(models.Model):
    """Déclaration et suivi d'une panne sur un point d'eau ou un équipement."""

    GRAVITE_CHOICES = [
        ('Faible', 'Faible'),
        ('Moyenne', 'Moyenne'),
        ('Élevée', 'Élevée'),
        ('Critique', 'Critique'),
    ]

    STATUT_CHOICES = [
        ('Nouveau signalement', 'Nouveau signalement'),
        ('En attente d’affectation', 'En attente d’affectation'),
        ('Technicien affecté', 'Technicien affecté'),
        ('En cours de réparation', 'En cours de réparation'),
        ('Résolu', 'Résolu'),
        ('Clôturé', 'Clôturé'),
    ]

    point_eau = models.ForeignKey(
        PointEau,
        on_delete=models.PROTECT,
        related_name='pannes',
        verbose_name="Point d'eau concerné",
    )
    equipement = models.ForeignKey(
        Equipement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pannes',
        verbose_name='Équipement concerné (optionnel)',
    )
    date_signalement = models.DateTimeField('Date de signalement', auto_now_add=True)
    description = models.TextField('Description de la panne')
    niveau_gravite = models.CharField('Niveau de gravité / Priorité', max_length=30, choices=GRAVITE_CHOICES, default='Moyenne')
    statut = models.CharField('Statut', max_length=50, choices=STATUT_CHOICES, default='Nouveau signalement')
    signale_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pannes_signalees',
        verbose_name='Utilisateur ayant effectué le signalement',
    )
    nom_declarant = models.CharField('Nom du déclarant', max_length=150, blank=True)
    photo = models.FileField('Photo (facultative)', upload_to='pannes/', null=True, blank=True)

    class Meta:
        verbose_name = 'Panne'
        verbose_name_plural = 'Pannes'
        ordering = ['id']

    def __str__(self):
        return f"Panne #{self.id} - {self.point_eau.identifiant} ({self.statut})"

    @property
    def technicien_nom(self):
        derniere = self.interventions.select_related('technicien').order_by('-id').first()
        if derniere and derniere.technicien:
            return derniere.technicien.nom_complet
        return ''

    def to_frontend_dict(self):
        declarant = self.nom_declarant
        if not declarant and self.signale_par:
            declarant = self.signale_par.get_display_name()
        return {
            'id': self.id,
            'pt': self.point_eau.identifiant,
            'd': self.description,
            'p': self.niveau_gravite,
            's': self.statut,
            'by': declarant or 'Resp. Local',
            'tech': self.technicien_nom,
        }
