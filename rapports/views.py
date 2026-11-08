import csv
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from localisation.models import Village
from points_eau.models import PointEau
from pannes.models import Panne
from interventions.models import Intervention
from stock.models import PieceDetachee
from techniciens.models import Technicien


@require_GET
def api_statistiques(request):
    """Calcule en temps réel les statistiques globales d'EauSolidaire depuis MySQL."""
    total_pts = PointEau.objects.count()
    fonct_pts = PointEau.objects.filter(etat_fonctionnement='Fonctionnel').count()
    en_panne = PointEau.objects.filter(etat_fonctionnement='En panne').count()
    taux = round((fonct_pts / total_pts) * 100) if total_pts > 0 else 0

    return JsonResponse({
        'ok': True,
        'stats': {
            'total_villages': Village.objects.count(),
            'total_points_eau': total_pts,
            'points_fonctionnels': fonct_pts,
            'points_en_panne': en_panne,
            'taux_disponibilite': taux,
            'total_pannes': Panne.objects.count(),
            'interventions_en_cours': Intervention.objects.filter(statut='En cours de réparation').count(),
            'total_techniciens': Technicien.objects.count(),
            'alertes_stock': PieceDetachee.objects.filter(
                quantite_disponible__lte=PieceDetachee._meta.get_field('seuil_alerte').default
            ).count(),
        },
    })


@require_GET
def export_points_eau_csv(request):
    """Exporte la liste complète des points d'eau au format CSV."""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="points-eau.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ref', 'nom', 'type', 'village', 'etat'])
    for pt in PointEau.objects.select_related('village').all():
        writer.writerow([pt.identifiant, pt.nom, pt.type_point, pt.village.nom, pt.etat_fonctionnement])
    return response
