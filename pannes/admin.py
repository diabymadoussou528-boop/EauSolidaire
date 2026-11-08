from django.contrib import admin
from .models import Panne


@admin.register(Panne)
class PanneAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'point_eau',
        'equipement',
        'niveau_gravite',
        'statut',
        'get_declarant',
        'get_technicien',
        'date_signalement',
    )
    list_filter = ('niveau_gravite', 'statut', 'point_eau__village__commune__cercle__region', 'date_signalement')
    search_fields = ('point_eau__identifiant', 'point_eau__nom', 'description', 'nom_declarant')

    @admin.display(description='Déclarant')
    def get_declarant(self, obj):
        return obj.nom_declarant or (obj.signale_par.get_display_name() if obj.signale_par else '—')

    @admin.display(description='Technicien affecté')
    def get_technicien(self, obj):
        return obj.technicien_nom or '—'
