from django.contrib import admin
from .models import RapportActivite


@admin.register(RapportActivite)
class RapportActiviteAdmin(admin.ModelAdmin):
    list_display = (
        'titre',
        'total_points_eau',
        'points_fonctionnels',
        'taux_disponibilite',
        'total_pannes',
        'interventions_terminees',
        'genere_par',
        'date_generation',
    )
    list_filter = ('date_generation',)
    search_fields = ('titre', 'observations')
