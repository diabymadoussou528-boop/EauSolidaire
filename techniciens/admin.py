from django.contrib import admin
from .models import Technicien


@admin.register(Technicien)
class TechnicienAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'specialite', 'region_affectation', 'telephone', 'email', 'disponible')
    list_filter = ('disponible', 'region_affectation')
    search_fields = ('nom_complet', 'specialite', 'telephone', 'email')
