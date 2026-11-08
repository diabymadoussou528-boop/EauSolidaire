from django.contrib import admin
from .models import Equipement


@admin.register(Equipement)
class EquipementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'nom', 'type_equipement', 'point_eau', 'etat', 'date_installation')
    list_filter = ('type_equipement', 'etat', 'point_eau__village__commune__cercle__region')
    search_fields = ('reference', 'nom', 'point_eau__identifiant', 'point_eau__nom', 'description')
