import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from points_eau.models import PointEau, HistoriqueEtatPointEau
from equipements.models import Equipement
from utilisateurs.models import Notification
from .models import Panne


@require_POST
def api_declarer_panne(request):
    """Enregistre le signalement d'une panne depuis l'espace Responsable local ou Administrateur."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)

    if request.content_type and request.content_type.startswith('multipart/form-data'):
        data = request.POST
        photo = request.FILES.get('photo')
    else:
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = request.POST
        photo = None

    pt_ref = (data.get('pt') or '').strip()
    eq_ref = (data.get('eq') or data.get('equipement') or '').strip()
    desc = (data.get('d') or data.get('description') or '').strip()
    gravite = (data.get('p') or data.get('niveau_gravite') or 'Moyenne').strip()
    by_name = (data.get('by') or '').strip() or request.user.get_display_name()

    pt = PointEau.objects.filter(identifiant=pt_ref).first()
    if not pt or not desc:
        return JsonResponse({'ok': False, 'error': "Le point d'eau et la description sont obligatoires."}, status=400)

    equipement = Equipement.objects.filter(reference=eq_ref, point_eau=pt).first() if eq_ref else None

    panne = Panne.objects.create(
        point_eau=pt,
        equipement=equipement,
        description=desc,
        niveau_gravite=gravite if gravite in dict(Panne.GRAVITE_CHOICES) else 'Moyenne',
        statut='Nouveau signalement',
        signale_par=request.user,
        nom_declarant=by_name,
        photo=photo,
    )

    if pt.etat_fonctionnement == 'Fonctionnel':
        pt.etat_fonctionnement = 'En panne'
        pt.save()
        HistoriqueEtatPointEau.objects.create(
            point_eau=pt,
            statut='En panne',
            note=f"Signalement panne #{panne.id}",
        )

    Notification.objects.create(utilisateur=None, message=f"Nouveau signalement : {pt.identifiant}")
    if request.user.frontend_role_code != 'admin':
        Notification.objects.create(utilisateur=request.user, message=f"Signalement enregistré : {pt.identifiant}")
    return JsonResponse({'ok': True, 'panne': panne.to_frontend_dict()})


@require_POST
def api_changer_statut_panne(request):
    """Met à jour le statut d'une panne (ex. Clôturé par l'administrateur)."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    panne_id = data.get('id')
    pt_ref = (data.get('pt') or '').strip()
    nouveau_statut = (data.get('s') or data.get('statut') or '').strip()

    panne = Panne.objects.filter(id=panne_id).select_related('point_eau').first()
    if not panne and pt_ref:
        panne = Panne.objects.filter(point_eau__identifiant=pt_ref).select_related('point_eau').order_by('-id').first()
    if not panne:
        return JsonResponse({'ok': False, 'error': 'Panne introuvable.'}, status=404)

    if nouveau_statut not in dict(Panne.STATUT_CHOICES):
        return JsonResponse({'ok': False, 'error': 'Statut invalide.'}, status=400)

    panne.statut = nouveau_statut
    panne.save()

    if nouveau_statut in ('Résolu', 'Clôturé'):
        pt = panne.point_eau
        pt.etat_fonctionnement = 'Fonctionnel'
        pt.save()
        HistoriqueEtatPointEau.objects.create(
            point_eau=pt,
            statut='Fonctionnel',
            note=f"Panne #{panne.id} : {nouveau_statut}",
        )

    Notification.objects.create(utilisateur=None, message=f"Statut modifié : {panne.point_eau.identifiant}")
    if panne.signale_par and panne.signale_par.frontend_role_code != 'admin':
        Notification.objects.create(
            utilisateur=panne.signale_par,
            message=f"Statut modifié ({nouveau_statut}) : {panne.point_eau.identifiant}",
        )
    return JsonResponse({'ok': True, 'panne': panne.to_frontend_dict()})
