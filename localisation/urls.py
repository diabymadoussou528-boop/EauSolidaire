from django.urls import path
from . import views

app_name = 'localisation'

urlpatterns = [
    path('villages/add/', views.api_add_village, name='api_add_village'),
    path('villages/delete/', views.api_delete_village, name='api_delete_village'),
]
