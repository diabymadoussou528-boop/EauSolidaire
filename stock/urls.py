from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('mouvement/', views.api_mouvement_stock, name='api_mouvement_stock'),
]
