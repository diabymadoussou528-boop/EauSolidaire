from django.contrib import admin
from .models import PieceDetachee, MouvementStock


@admin.register(PieceDetachee)
class PieceDetacheeAdmin(admin.ModelAdmin):
    list_display = ('reference', 'nom', 'quantite_disponible', 'seuil_alerte', 'prix_unitaire', 'est_en_alerte')
    list_filter = ('seuil_alerte',)
    search_fields = ('reference', 'nom', 'description')


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ('date_mouvement', 'piece', 'type_mouvement', 'quantite', 'intervention', 'effectue_par', 'commentaire')
    list_filter = ('type_mouvement', 'piece', 'date_mouvement')
    search_fields = ('piece__nom', 'piece__reference', 'commentaire')
