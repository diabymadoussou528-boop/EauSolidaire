import json
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from .models import Village
from .forms import VillageQuickCreateForm


def _check_admin_or_resp(user):
    return user.is_authenticated and (user.is_superuser or user.role in ('ADMIN', 'RESPONSABLE'))


@require_POST
def api_add_village(request):
    """Ajoute un village en respectant la hiérarchie Région → Cercle → Commune → Village."""
    if not _check_admin_or_resp(request.user):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    form = VillageQuickCreateForm(data)
    if not form.is_valid():
        return JsonResponse({'ok': False, 'error': 'Tous les champs géographiques sont requis.'}, status=400)

    village = form.save()
    return JsonResponse({'ok': True, 'village': village.to_frontend_dict()})


@require_http_methods(["POST", "DELETE"])
def api_delete_village(request):
    """Supprime un village s'il n'a aucun point d'eau rattaché."""
    if not _check_admin_or_resp(request.user):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    nom = (data.get('n') or data.get('nom') or '').strip()
    village_id = data.get('id')

    village = None
    if village_id:
        village = Village.objects.filter(id=village_id).first()
    if not village and nom:
        village = Village.objects.filter(nom=nom).first()

    if not village:
        return JsonResponse({'ok': False, 'error': 'Village introuvable.'}, status=404)

    if village.points_eau.exists():
        return JsonResponse({'ok': False, 'error': 'Suppression impossible : des points d’eau en dépendent'}, status=400)

    try:
        village.delete()
    except ProtectedError:
        return JsonResponse({'ok': False, 'error': 'Suppression impossible : des éléments en dépendent'}, status=400)

    return JsonResponse({'ok': True})
