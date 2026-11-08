from django.conf import settings
from django.db import models


class RapportActivite(models.Model):
    """Rapport statistique ou export d'activité généré sur la plateforme."""

    titre = models.CharField('Titre du rapport', max_length=200)
    periode_debut = models.DateField('Début de période', null=True, blank=True)
    periode_fin = models.DateField('Fin de période', null=True, blank=True)
    total_points_eau = models.PositiveIntegerField("Nombre total de points d'eau", default=0)
    points_fonctionnels = models.PositiveIntegerField('Points fonctionnels', default=0)
    taux_disponibilite = models.FloatField('Taux de disponibilité (%)', default=0.0)
    total_pannes = models.PositiveIntegerField('Total pannes signalées', default=0)
    interventions_terminees = models.PositiveIntegerField('Interventions terminées', default=0)
    observations = models.TextField('Observations / Synthèse', blank=True)
    genere_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='rapports_generes',
        verbose_name='Généré par',
    )
    date_generation = models.DateTimeField('Date de génération', auto_now_add=True)

    class Meta:
        verbose_name = "Rapport d'activité"
        verbose_name_plural = "Rapports d'activité"
        ordering = ['-date_generation']

    def __str__(self):
        return f"{self.titre} ({self.date_generation:%d/%m/%Y})"
