from django import forms
from .models import Region, Cercle, Commune, Village


class VillageQuickCreateForm(forms.Form):
    n = forms.CharField(label='Village', max_length=100)
    c = forms.CharField(label='Commune', max_length=100)
    ce = forms.CharField(label='Cercle', max_length=100)
    r = forms.CharField(label='Région', max_length=100)

    def save(self):
        region_nom = self.cleaned_data['r'].strip()
        cercle_nom = self.cleaned_data['ce'].strip()
        commune_nom = self.cleaned_data['c'].strip()
        village_nom = self.cleaned_data['n'].strip()

        region, _ = Region.objects.get_or_create(nom=region_nom)
        cercle, _ = Cercle.objects.get_or_create(nom=cercle_nom, region=region)
        commune, _ = Commune.objects.get_or_create(nom=commune_nom, cercle=cercle)
        village, _ = Village.objects.get_or_create(nom=village_nom, commune=commune)
        return village
