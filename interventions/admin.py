from django.contrib import admin
from .models import Intervention, PieceUtiliseeIntervention


class PieceUtiliseeInline(admin.TabularInline):
    model = PieceUtiliseeIntervention
    extra = 0


@admin.register(Intervention)
class InterventionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'panne',
        'technicien',
        'statut',
        'date_debut',
        'date_fin',
        'cout_eventuel',
    )
    list_filter = ('statut', 'technicien', 'date_affectation')
    search_fields = ('panne__point_eau__identifiant', 'technicien__nom_complet', 'travaux_realises')
    inlines = [PieceUtiliseeInline]


@admin.register(PieceUtiliseeIntervention)
class PieceUtiliseeInterventionAdmin(admin.ModelAdmin):
    list_display = ('intervention', 'piece', 'quantite')
    list_filter = ('piece',)
