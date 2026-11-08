from django.urls import path
from . import views

app_name = 'techniciens'

urlpatterns = [
    path('', views.api_list_techniciens, name='api_list_techniciens'),
]
