from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Utilisateur, Notification, MessageContact


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ('email', 'nom_complet', 'role', 'village', 'telephone', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'village')
    search_fields = ('email', 'nom_complet', 'username', 'telephone')
    ordering = ('email',)

    fieldsets = UserAdmin.fieldsets + (
        ('Informations EauSolidaire', {
            'fields': ('nom_complet', 'telephone', 'role', 'village'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations EauSolidaire', {
            'fields': ('email', 'nom_complet', 'telephone', 'role', 'village'),
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('message', 'utilisateur', 'lue', 'date_creation')
    list_filter = ('lue', 'date_creation')
    search_fields = ('message',)


@admin.register(MessageContact)
class MessageContactAdmin(admin.ModelAdmin):
    list_display = ('sujet', 'nom_complet', 'email', 'traite', 'date_envoi')
    list_filter = ('sujet', 'traite', 'date_envoi')
    search_fields = ('nom_complet', 'email', 'message')
