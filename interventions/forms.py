from django import forms
from .models import Intervention


class InterventionForm(forms.ModelForm):
    class Meta:
        model = Intervention
        fields = ['panne', 'technicien', 'date_debut', 'date_fin', 'travaux_realises', 'cout_eventuel', 'statut']
