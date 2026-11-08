import json
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from pannes.models import Panne
from points_eau.models import HistoriqueEtatPointEau
from stock.models import PieceDetachee, MouvementStock
from techniciens.models import Technicien
from utilisateurs.models import Notification
from .models import Intervention, PieceUtiliseeIntervention


@require_POST
def api_affecter_technicien(request):
    """Affecte un technicien à une panne et crée l'intervention correspondante."""
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    panne_id = data.get('id')
    tech_nom = (data.get('t') or data.get('technicien') or '').strip()

    panne = Panne.objects.filter(id=panne_id).select_related('point_eau').first()
    if not panne or not tech_nom:
        return JsonResponse({'ok': False, 'error': 'Panne ou technicien invalide.'}, status=400)

    technicien, _ = Technicien.objects.get_or_create(nom_complet=tech_nom)

    intervention = panne.interventions.order_by('-id').first()
    if intervention:
        intervention.technicien = technicien
        intervention.statut = 'Affectée'
        intervention.save()
    else:
        intervention = Intervention.objects.create(
            panne=panne,
            technicien=technicien,
            statut='Affectée',
        )

    panne.statut = 'Technicien affecté'
    panne.save()

    Notification.objects.create(message=f"Intervention créée pour {technicien.nom_complet} ({panne.point_eau.identifiant})")
    return JsonResponse({'ok': True, 'panne': panne.to_frontend_dict(), 'intervention_id': intervention.id})


@require_POST
def api_demarrer_intervention(request):
    """Démarre une intervention par le technicien affecté."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    panne_id = data.get('id')
    panne = Panne.objects.filter(id=panne_id).select_related('point_eau').first()
    if not panne:
        return JsonResponse({'ok': False, 'error': 'Panne introuvable.'}, status=404)

    intervention = panne.interventions.order_by('-id').first()
    if intervention:
        intervention.statut = 'En cours de réparation'
        intervention.date_debut = timezone.now()
        intervention.save()

    panne.statut = 'En cours de réparation'
    panne.save()

    pt = panne.point_eau
    pt.etat_fonctionnement = 'En maintenance'
    pt.save()
    HistoriqueEtatPointEau.objects.create(
        point_eau=pt,
        statut='En maintenance',
        note='Intervention démarrée',
    )

    Notification.objects.create(message=f"Statut modifié : {pt.identifiant}")
    return JsonResponse({'ok': True, 'panne': panne.to_frontend_dict()})


@require_POST
def api_terminer_intervention(request):
    """Clôture l'intervention du technicien, enregistre les travaux réalisés et déduit les pièces utilisées."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    panne_id = data.get('id')
    compte_rendu = (data.get('r') or data.get('travaux_realises') or '').strip()
    piece_ref = (data.get('piece_ref') or '').strip()
    quantite = int(data.get('q') or 1)
    cout = data.get('cout') or 0

    panne = Panne.objects.filter(id=panne_id).select_related('point_eau').first()
    if not panne or not compte_rendu:
        return JsonResponse({'ok': False, 'error': 'Compte rendu obligatoire.'}, status=400)

    intervention = panne.interventions.order_by('-id').first()
    if not intervention:
        tech = Technicien.objects.filter(utilisateur=request.user).first() or Technicien.objects.first()
        intervention = Intervention.objects.create(
            panne=panne,
            technicien=tech,
            date_debut=timezone.now(),
        )

    mvt_label = None
    if piece_ref:
        piece = PieceDetachee.objects.filter(reference=piece_ref).first()
        if not piece:
            return JsonResponse({'ok': False, 'error': 'Pièce détachée introuvable.'}, status=404)
        if quantite > piece.quantite_disponible:
            return JsonResponse({'ok': False, 'error': 'Stock insuffisant'}, status=400)

        piece.quantite_disponible -= quantite
        piece.save()

        PieceUtiliseeIntervention.objects.create(
            intervention=intervention,
            piece=piece,
            quantite=quantite,
        )
        mvt_label = f"−{quantite} {piece.nom} (intervention {panne.point_eau.identifiant})"
        MouvementStock.objects.create(
            piece=piece,
            type_mouvement='SORTIE',
            quantite=quantite,
            intervention=intervention,
            effectue_par=request.user,
            commentaire=mvt_label,
        )
        if piece.quantite_disponible <= piece.seuil_alerte:
            Notification.objects.create(message=f"Stock faible : {piece.nom}")

    intervention.travaux_realises = compte_rendu
    intervention.date_fin = timezone.now()
    intervention.statut = 'Terminée'
    try:
        intervention.cout_eventuel = float(cout)
    except (TypeError, ValueError):
        pass
    intervention.save()

    panne.statut = 'Résolu'
    panne.save()

    pt = panne.point_eau
    pt.etat_fonctionnement = 'Fonctionnel'
    pt.save()
    HistoriqueEtatPointEau.objects.create(
        point_eau=pt,
        statut='Fonctionnel',
        note=f"Intervention terminée : {compte_rendu[:80]}",
    )

    Notification.objects.create(message=f"Intervention terminée : {pt.identifiant}")
    return JsonResponse({
        'ok': True,
        'panne': panne.to_frontend_dict(),
        'mouvement': mvt_label,
    })
