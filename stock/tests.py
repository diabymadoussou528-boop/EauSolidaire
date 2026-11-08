from django.test import TestCase
from .models import PieceDetachee, MouvementStock


class StockModelTests(TestCase):
    def test_alerte_stock(self):
        piece = PieceDetachee.objects.create(
            nom='Clapet de pompe manuelle',
            reference='P-02',
            quantite_disponible=3,
            seuil_alerte=4,
        )
        self.assertTrue(piece.est_en_alerte)
        mvt = MouvementStock.objects.create(piece=piece, type_mouvement='ENTREE', quantite=5)
        self.assertIn('+5', str(mvt))
