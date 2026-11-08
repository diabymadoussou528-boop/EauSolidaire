from django.urls import path, include
from . import views

app_name = 'suivi'

urlpatterns = [
    path('', views.accueil, name='accueil'),
    path('api/state/', views.api_state, name='api_state'),
    path('api/auth/', include('utilisateurs.urls')),
    path('api/localisation/', include('localisation.urls')),
    path('api/points-eau/', include('points_eau.urls')),
    path('api/equipements/', include('equipements.urls')),
    path('api/pannes/', include('pannes.urls')),
    path('api/interventions/', include('interventions.urls')),
    path('api/techniciens/', include('techniciens.urls')),
    path('api/stock/', include('stock.urls')),
    path('api/rapports/', include('rapports.urls')),
]
