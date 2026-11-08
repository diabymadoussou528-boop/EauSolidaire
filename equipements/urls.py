from django.urls import path
from . import views

app_name = 'equipements'

urlpatterns = [
    path('', views.api_list_equipements, name='api_list_equipements'),
    path('add/', views.api_add_equipement, name='api_add_equipement'),
    path('etat/', views.api_update_etat_equipement, name='api_update_etat_equipement'),
    path('delete/', views.api_delete_equipement, name='api_delete_equipement'),
]
