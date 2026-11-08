from django.conf import settings
from django.db import models


class PieceDetachee(models.Model):
    """Pièce détachée en stock pour la maintenance des points d'eau."""

    nom = models.CharField('Nom de la pièce', max_length=150)
    reference = models.CharField('Référence', max_length=50, unique=True)
    quantite_disponible = models.PositiveIntegerField('Quantité disponible', default=0)
    seuil_alerte = models.PositiveIntegerField("Seuil d'alerte minimum", default=5)
    prix_unitaire = models.DecimalField('Prix unitaire (FCFA)', max_digits=12, decimal_places=2, default=0)
    description = models.TextField('Description', blank=True)

    class Meta:
        verbose_name = 'Pièce détachée'
        verbose_name_plural = 'Pièces détachées'
        ordering = ['reference']

    def __str__(self):
        return f"{self.nom} ({self.reference}) - Stock: {self.quantite_disponible}"

    @property
    def est_en_alerte(self):
        return self.quantite_disponible <= self.seuil_alerte

    def to_frontend_dict(self):
        return {
            'id': self.id,
            'n': self.nom,
            'ref': self.reference,
            'q': self.quantite_disponible,
            'min': self.seuil_alerte,
        }


class MouvementStock(models.Model):
    """Historique des entrées et sorties de stock."""

    TYPE_CHOICES = [
        ('ENTREE', 'Entrée'),
        ('SORTIE', 'Sortie'),
    ]

    piece = models.ForeignKey(
        PieceDetachee,
        on_delete=models.PROTECT,
        related_name='mouvements',
        verbose_name='Pièce détachée',
    )
    type_mouvement = models.CharField('Type de mouvement', max_length=10, choices=TYPE_CHOICES)
    quantite = models.PositiveIntegerField('Quantité')
    intervention = models.ForeignKey(
        'interventions.Intervention',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mouvements_stock',
        verbose_name='Intervention associée',
    )
    effectue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mouvements_stock',
        verbose_name='Effectué par',
    )
    commentaire = models.CharField('Libellé / Commentaire', max_length=255, blank=True)
    date_mouvement = models.DateTimeField('Date du mouvement', auto_now_add=True)

    class Meta:
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'
        ordering = ['-date_mouvement', '-id']

    def __str__(self):
        signe = '+' if self.type_mouvement == 'ENTREE' else '−'
        if self.commentaire:
            return self.commentaire
        return f"{signe}{self.quantite} {self.piece.nom}"
