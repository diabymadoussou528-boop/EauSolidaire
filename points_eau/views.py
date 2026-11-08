import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from localisation.models import Village
from .models import PointEau, HistoriqueEtatPointEau


def _valider_gps_mali(lat, lon):
    if lat is None and lon is None:
        return True
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False
    return 10.0 <= lat_f <= 25.3 and -12.5 <= lon_f <= 4.4


@require_POST
def api_add_point_eau(request):
    """Enregistre un nouveau point d'eau dans MySQL."""
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or data.get('identifiant') or '').strip()
    nom = (data.get('n') or data.get('nom') or '').strip()
    type_pt = (data.get('t') or data.get('type_point') or 'Forage').strip()
    village_nom = (data.get('v') or data.get('village') or '').strip()
    desc = (data.get('desc') or data.get('description') or '').strip()
    la_raw = data.get('la')
    lo_raw = data.get('lo')

    if not ref or not nom or not village_nom:
        return JsonResponse({'ok': False, 'error': 'Référence, nom et village sont obligatoires.'}, status=400)

    if PointEau.objects.filter(identifiant__iexact=ref).exists():
        return JsonResponse({'ok': False, 'error': 'Référence déjà utilisée'}, status=400)

    village = Village.objects.filter(nom=village_nom).first()
    if not village:
        return JsonResponse({'ok': False, 'error': 'Village introuvable.'}, status=404)

    lat = float(la_raw) if la_raw not in (None, '') else None
    lon = float(lo_raw) if lo_raw not in (None, '') else None

    if (lat is not None or lon is not None) and not _valider_gps_mali(lat, lon):
        return JsonResponse(
            {'ok': False, 'error': 'Position invalide : latitude 10 à 25, longitude −12,5 à 4,4'},
            status=400,
        )

    pt = PointEau.objects.create(
        identifiant=ref,
        nom=nom,
        type_point=type_pt if type_pt in ('Forage', 'Puits', 'Autre') else 'Autre',
        village=village,
        latitude=lat,
        longitude=lon,
        etat_fonctionnement='Fonctionnel',
        description=desc,
    )
    HistoriqueEtatPointEau.objects.create(
        point_eau=pt,
        statut='Fonctionnel',
        note='Création',
    )

    return JsonResponse({'ok': True, 'point': pt.to_frontend_dict()})


@require_POST
def api_update_etat_point_eau(request):
    """Met à jour l'état de fonctionnement d'un point d'eau."""
    if not request.user.is_authenticated or request.user.frontend_role_code not in ('admin', 'tech'):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or '').strip()
    statut = (data.get('s') or data.get('etat') or '').strip()

    pt = PointEau.objects.filter(identifiant=ref).first()
    if not pt:
        return JsonResponse({'ok': False, 'error': "Point d'eau introuvable."}, status=404)

    valid_statuts = dict(PointEau.ETAT_CHOICES).keys()
    if statut not in valid_statuts:
        return JsonResponse({'ok': False, 'error': 'État invalide.'}, status=400)

    pt.etat_fonctionnement = statut
    pt.save()
    HistoriqueEtatPointEau.objects.create(point_eau=pt, statut=statut)

    return JsonResponse({'ok': True, 'point': pt.to_frontend_dict()})


@require_POST
def api_update_position_point_eau(request):
    """Met à jour les coordonnées GPS d'un point d'eau."""
    if not request.user.is_authenticated or request.user.frontend_role_code not in ('admin', 'tech'):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or '').strip()
    la_raw = data.get('la')
    lo_raw = data.get('lo')

    pt = PointEau.objects.filter(identifiant=ref).first()
    if not pt:
        return JsonResponse({'ok': False, 'error': "Point d'eau introuvable."}, status=404)

    if not _valider_gps_mali(la_raw, lo_raw):
        return JsonResponse(
            {'ok': False, 'error': 'Position invalide : latitude 10 à 25, longitude −12,5 à 4,4'},
            status=400,
        )

    pt.latitude = float(la_raw)
    pt.longitude = float(lo_raw)
    pt.save()
    HistoriqueEtatPointEau.objects.create(
        point_eau=pt,
        statut=pt.etat_fonctionnement,
        note='Position mise à jour',
    )

    return JsonResponse({'ok': True, 'point': pt.to_frontend_dict()})
