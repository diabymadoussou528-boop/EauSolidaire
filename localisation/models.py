from django.db import models


class Region(models.Model):
    """Région administrative du Mali."""

    nom = models.CharField('Nom de la région', max_length=100, unique=True)
    code = models.CharField('Code région', max_length=20, blank=True)
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Région'
        verbose_name_plural = 'Régions'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Cercle(models.Model):
    """Cercle administratif rattaché à une région."""

    nom = models.CharField('Nom du cercle', max_length=100)
    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name='cercles',
        verbose_name='Région',
    )
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Cercle'
        verbose_name_plural = 'Cercles'
        ordering = ['region__nom', 'nom']
        unique_together = [('nom', 'region')]

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class Commune(models.Model):
    """Commune rattachée à un cercle."""

    nom = models.CharField('Nom de la commune', max_length=100)
    cercle = models.ForeignKey(
        Cercle,
        on_delete=models.PROTECT,
        related_name='communes',
        verbose_name='Cercle',
    )
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Commune'
        verbose_name_plural = 'Communes'
        ordering = ['cercle__nom', 'nom']
        unique_together = [('nom', 'cercle')]

    def __str__(self):
        return f"{self.nom} ({self.cercle.nom})"


class Village(models.Model):
    """Village rattaché à une commune (Région → Cercle → Commune → Village)."""

    nom = models.CharField('Nom du village', max_length=100)
    commune = models.ForeignKey(
        Commune,
        on_delete=models.PROTECT,
        related_name='villages',
        verbose_name='Commune',
    )
    population_estimee = models.PositiveIntegerField('Population estimée', null=True, blank=True)
    latitude = models.FloatField('Latitude', null=True, blank=True)
    longitude = models.FloatField('Longitude', null=True, blank=True)
    date_creation = models.DateTimeField('Date de création', auto_now_add=True)

    class Meta:
        verbose_name = 'Village'
        verbose_name_plural = 'Villages'
        ordering = ['nom']
        unique_together = [('nom', 'commune')]

    def __str__(self):
        return f"{self.nom} ({self.commune.cercle.region.nom})"

    @property
    def cercle(self):
        return self.commune.cercle

    @property
    def region(self):
        return self.commune.cercle.region

    def to_frontend_dict(self):
        return {
            'id': self.id,
            'n': self.nom,
            'c': self.commune.nom,
            'ce': self.commune.cercle.nom,
            'r': self.commune.cercle.region.nom,
        }
