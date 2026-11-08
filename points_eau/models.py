from django.db import models
from localisation.models import Village


class PointEau(models.Model):
    """Point d'eau suivi par la plateforme EauSolidaire."""

    TYPE_CHOICES = [
        ('Forage', 'Forage'),
        ('Puits', 'Puits'),
        ('Autre', 'Autre'),
    ]

    ETAT_CHOICES = [
        ('Fonctionnel', 'Fonctionnel'),
        ('En panne', 'En panne'),
        ('En maintenance', 'En maintenance'),
        ('Hors service', 'Hors service'),
    ]

    identifiant = models.CharField("Identifiant / Référence", max_length=50, unique=True)
    nom = models.CharField("Nom du point d'eau", max_length=150)
    type_point = models.CharField("Type de point d'eau", max_length=50, choices=TYPE_CHOICES, default='Forage')
    village = models.ForeignKey(
        Village,
        on_delete=models.PROTECT,
        related_name='points_eau',
        verbose_name='Village',
    )
    localisation_detail = models.CharField('Précision de localisation', max_length=200, blank=True)
    latitude = models.FloatField('Latitude GPS', null=True, blank=True)
    longitude = models.FloatField('Longitude GPS', null=True, blank=True)
    etat_fonctionnement = models.CharField(
        'État de fonctionnement',
        max_length=50,
        choices=ETAT_CHOICES,
        default='Fonctionnel',
    )
    description = models.TextField('Description', blank=True)
    date_creation = models.DateField('Date de création / mise en service', auto_now_add=True)
    date_modification = models.DateTimeField('Dernière mise à jour', auto_now=True)

    class Meta:
        verbose_name = "Point d'eau"
        verbose_name_plural = "Points d'eau"
        ordering = ['identifiant']

    def __str__(self):
        return f"{self.identifiant} - {self.nom} ({self.village.nom})"

    def to_frontend_dict(self):
        logs = [
            {
                'd': h.date_changement.strftime('%d/%m/%Y'),
                's': h.statut,
                'n': h.note,
            }
            for h in self.historiques_etat.all()[:15]
        ]
        if not logs:
            logs = [{'d': self.date_creation.strftime('%d/%m/%Y'), 's': self.etat_fonctionnement, 'n': 'Création'}]
        return {
            'id': self.id,
            'ref': self.identifiant,
            'n': self.nom,
            't': self.type_point,
            'v': self.village.nom,
            's': self.etat_fonctionnement,
            'la': self.latitude,
            'lo': self.longitude,
            'desc': self.description,
            'log': logs,
        }


class HistoriqueEtatPointEau(models.Model):
    """Journal de suivi des états et positions d'un point d'eau."""

    point_eau = models.ForeignKey(
        PointEau,
        on_delete=models.CASCADE,
        related_name='historiques_etat',
        verbose_name="Point d'eau",
    )
    statut = models.CharField('Statut', max_length=50, blank=True)
    note = models.CharField('Note / Observation', max_length=255, blank=True)
    date_changement = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = "Historique d'état d'un point d'eau"
        verbose_name_plural = "Historiques d'état des points d'eau"
        ordering = ['-date_changement']

    def __str__(self):
        return f"{self.point_eau.identifiant} - {self.statut} ({self.date_changement:%d/%m/%Y})"
