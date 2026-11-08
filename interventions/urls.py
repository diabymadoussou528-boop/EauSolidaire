from django.urls import path
from . import views

app_name = 'interventions'

urlpatterns = [
    path('affecter/', views.api_affecter_technicien, name='api_affecter_technicien'),
    path('demarrer/', views.api_demarrer_intervention, name='api_demarrer_intervention'),
    path('terminer/', views.api_terminer_intervention, name='api_terminer_intervention'),
]
