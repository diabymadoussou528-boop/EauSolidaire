from django import forms
from .models import Panne


class PanneForm(forms.ModelForm):
    class Meta:
        model = Panne
        fields = ['point_eau', 'equipement', 'description', 'niveau_gravite', 'photo']
