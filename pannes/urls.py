from django.urls import path
from . import views

app_name = 'pannes'

urlpatterns = [
    path('add/', views.api_declarer_panne, name='api_declarer_panne'),
    path('statut/', views.api_changer_statut_panne, name='api_changer_statut_panne'),
]
