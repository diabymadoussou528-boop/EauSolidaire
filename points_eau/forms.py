from django import forms
from .models import PointEau


class PointEauForm(forms.ModelForm):
    class Meta:
        model = PointEau
        fields = [
            'identifiant',
            'nom',
            'type_point',
            'village',
            'localisation_detail',
            'latitude',
            'longitude',
            'etat_fonctionnement',
            'description',
        ]
