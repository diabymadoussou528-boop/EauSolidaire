from django.urls import path
from . import views

app_name = 'points_eau'

urlpatterns = [
    path('add/', views.api_add_point_eau, name='api_add_point_eau'),
    path('etat/', views.api_update_etat_point_eau, name='api_update_etat_point_eau'),
    path('position/', views.api_update_position_point_eau, name='api_update_position_point_eau'),
]
