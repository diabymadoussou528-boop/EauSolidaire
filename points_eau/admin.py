from django.contrib import admin
from .models import PointEau, HistoriqueEtatPointEau


class HistoriqueEtatInline(admin.TabularInline):
    model = HistoriqueEtatPointEau
    extra = 0
    readonly_fields = ('date_changement',)


@admin.register(PointEau)
class PointEauAdmin(admin.ModelAdmin):
    list_display = (
        'identifiant',
        'nom',
        'type_point',
        'village',
        'get_region',
        'etat_fonctionnement',
        'latitude',
        'longitude',
        'date_creation',
    )
    list_filter = ('type_point', 'etat_fonctionnement', 'village__commune__cercle__region', 'village')
    search_fields = ('identifiant', 'nom', 'village__nom', 'description')
    inlines = [HistoriqueEtatInline]

    @admin.display(description='Région')
    def get_region(self, obj):
        return obj.village.region.nom


@admin.register(HistoriqueEtatPointEau)
class HistoriqueEtatPointEauAdmin(admin.ModelAdmin):
    list_display = ('point_eau', 'statut', 'note', 'date_changement')
    list_filter = ('statut', 'date_changement')
    search_fields = ('point_eau__identifiant', 'point_eau__nom', 'note')
