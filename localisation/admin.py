from django.contrib import admin
from .models import Region, Cercle, Commune, Village


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'date_creation')
    search_fields = ('nom', 'code')


@admin.register(Cercle)
class CercleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'date_creation')
    list_filter = ('region',)
    search_fields = ('nom', 'region__nom')


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('nom', 'cercle', 'get_region', 'date_creation')
    list_filter = ('cercle__region', 'cercle')
    search_fields = ('nom', 'cercle__nom', 'cercle__region__nom')

    @admin.display(description='Région')
    def get_region(self, obj):
        return obj.cercle.region.nom


@admin.register(Village)
class VillageAdmin(admin.ModelAdmin):
    list_display = ('nom', 'commune', 'get_cercle', 'get_region', 'population_estimee')
    list_filter = ('commune__cercle__region', 'commune__cercle', 'commune')
    search_fields = ('nom', 'commune__nom', 'commune__cercle__nom', 'commune__cercle__region__nom')

    @admin.display(description='Cercle')
    def get_cercle(self, obj):
        return obj.commune.cercle.nom

    @admin.display(description='Région')
    def get_region(self, obj):
        return obj.commune.cercle.region.nom
