from django.urls import path
from . import views

app_name = 'rapports'

urlpatterns = [
    path('statistiques/', views.api_statistiques, name='api_statistiques'),
    path('export-csv/', views.export_points_eau_csv, name='export_points_eau_csv'),
]
