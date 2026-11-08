from django import forms
from .models import Equipement


class EquipementForm(forms.ModelForm):
    class Meta:
        model = Equipement
        fields = ['point_eau', 'nom', 'type_equipement', 'reference', 'date_installation', 'etat', 'description']
