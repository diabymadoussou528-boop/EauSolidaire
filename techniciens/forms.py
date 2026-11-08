from django import forms
from .models import Technicien


class TechnicienForm(forms.ModelForm):
    class Meta:
        model = Technicien
        fields = ['utilisateur', 'nom_complet', 'telephone', 'email', 'specialite', 'region_affectation', 'disponible']
