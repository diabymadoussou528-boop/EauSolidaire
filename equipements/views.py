import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from points_eau.models import PointEau
from .models import Equipement


@require_GET
def api_list_equipements(request):
    items = [e.to_frontend_dict() for e in Equipement.objects.select_related('point_eau').all()]
    return JsonResponse({'ok': True, 'equipements': items})


@require_POST
def api_add_equipement(request):
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    pt_ref = (data.get('pt') or data.get('point_eau') or '').strip()
    nom = (data.get('nom') or '').strip()
    ref = (data.get('ref') or data.get('reference') or '').strip()
    type_eq = (data.get('type') or data.get('type_equipement') or 'Pompe manuelle').strip()
    etat = (data.get('etat') or 'Fonctionnel').strip()
    desc = (data.get('description') or '').strip()

    pt = PointEau.objects.filter(identifiant=pt_ref).first()
    if not pt or not nom or not ref:
        return JsonResponse({'ok': False, 'error': "Point d'eau, nom et référence sont requis."}, status=400)

    if Equipement.objects.filter(reference__iexact=ref).exists():
        return JsonResponse({'ok': False, 'error': 'Référence équipement déjà utilisée.'}, status=400)

    eq = Equipement.objects.create(
        point_eau=pt,
        nom=nom,
        type_equipement=type_eq,
        reference=ref,
        etat=etat,
        description=desc,
    )
    return JsonResponse({'ok': True, 'equipement': eq.to_frontend_dict()})


@require_POST
def api_update_etat_equipement(request):
    if not request.user.is_authenticated or request.user.frontend_role_code not in ('admin', 'tech'):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or data.get('reference') or '').strip()
    eq_id = data.get('id')
    etat = (data.get('etat') or '').strip()

    eq = Equipement.objects.filter(id=eq_id).first() if eq_id else Equipement.objects.filter(reference=ref).first()
    if not eq or not etat:
        return JsonResponse({'ok': False, 'error': 'Équipement introuvable ou état invalide.'}, status=404)

    eq.etat = etat
    eq.save(update_fields=['etat'])
    return JsonResponse({'ok': True, 'equipement': eq.to_frontend_dict()})


@require_POST
def api_delete_equipement(request):
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or data.get('reference') or '').strip()
    eq_id = data.get('id')

    eq = Equipement.objects.filter(id=eq_id).first() if eq_id else Equipement.objects.filter(reference=ref).first()
    if not eq:
        return JsonResponse({'ok': False, 'error': 'Équipement introuvable.'}, status=404)

    eq.delete()
    return JsonResponse({'ok': True})

