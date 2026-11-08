import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from utilisateurs.models import Notification
from .models import PieceDetachee, MouvementStock


@require_POST
def api_mouvement_stock(request):
    """Enregistre une entrée ou sortie de stock."""
    if not request.user.is_authenticated or request.user.frontend_role_code not in ('admin', 'tech'):
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    ref = (data.get('ref') or '').strip()
    piece_id = data.get('id')
    sens = int(data.get('s', 1))
    quantite = int(data.get('q', 0))

    if quantite <= 0:
        return JsonResponse({'ok': False, 'error': 'La quantité doit être supérieure à 0.'}, status=400)

    piece = None
    if piece_id:
        piece = PieceDetachee.objects.filter(id=piece_id).first()
    if not piece and ref:
        piece = PieceDetachee.objects.filter(reference=ref).first()

    if not piece:
        return JsonResponse({'ok': False, 'error': 'Pièce détachée introuvable.'}, status=404)

    if sens < 0 and quantite > piece.quantite_disponible:
        Notification.objects.create(message=f"Stock insuffisant : {piece.nom}")
        return JsonResponse(
            {'ok': False, 'error': f"Stock insuffisant : {piece.quantite_disponible} disponible(s)"},
            status=400,
        )

    if sens > 0:
        piece.quantite_disponible += quantite
        type_mvt = 'ENTREE'
        libelle = f"+{quantite} {piece.nom}"
    else:
        piece.quantite_disponible -= quantite
        type_mvt = 'SORTIE'
        libelle = f"−{quantite} {piece.nom}"

    piece.save()
    MouvementStock.objects.create(
        piece=piece,
        type_mouvement=type_mvt,
        quantite=quantite,
        effectue_par=request.user,
        commentaire=libelle,
    )

    if piece.quantite_disponible <= piece.seuil_alerte:
        Notification.objects.create(message=f"Stock faible : {piece.nom}")

    return JsonResponse({
        'ok': True,
        'piece': piece.to_frontend_dict(),
        'mouvement': libelle,
    })
