from django.urls import path
from . import views

app_name = 'utilisateurs'

urlpatterns = [
    path('login/', views.api_login, name='api_login'),
    path('logout/', views.api_logout, name='api_logout'),
    path('notifications/clear/', views.api_clear_notifications, name='api_clear_notifications'),
    path('contact/', views.api_contact, name='api_contact'),
    path('password-reset/', views.api_password_reset_request, name='api_password_reset_request'),
    path('password-reset/confirm/', views.api_password_reset_confirm, name='api_password_reset_confirm'),
]
