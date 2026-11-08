from django import forms
from .models import PieceDetachee, MouvementStock


class PieceDetacheeForm(forms.ModelForm):
    class Meta:
        model = PieceDetachee
        fields = ['nom', 'reference', 'quantite_disponible', 'seuil_alerte', 'prix_unitaire', 'description']


class MouvementStockForm(forms.ModelForm):
    class Meta:
        model = MouvementStock
        fields = ['piece', 'type_mouvement', 'quantite', 'commentaire']
