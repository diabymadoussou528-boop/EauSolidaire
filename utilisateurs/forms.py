from django import forms
from .models import Utilisateur, MessageContact


class ConnexionForm(forms.Form):
    u = forms.CharField(label="Identifiant ou e-mail", max_length=150)
    p = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)


class MessageContactForm(forms.ModelForm):
    class Meta:
        model = MessageContact
        fields = ['sujet', 'nom_complet', 'email', 'message']
