from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Technicien


@require_GET
def api_list_techniciens(request):
    techs = [
        {
            'id': t.id,
            'nom': t.nom_complet,
            'specialite': t.specialite,
            'disponible': t.disponible,
            'region': t.region_affectation.nom if t.region_affectation else '',
        }
        for t in Technicien.objects.select_related('region_affectation').all()
    ]
    return JsonResponse({'ok': True, 'techniciens': techs})
