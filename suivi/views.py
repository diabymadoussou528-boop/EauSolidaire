from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from localisation.models import Region, Cercle, Commune, Village
from points_eau.models import PointEau, HistoriqueEtatPointEau
from equipements.models import Equipement
from pannes.models import Panne
from interventions.models import Intervention
from techniciens.models import Technicien
from stock.models import PieceDetachee, MouvementStock
from utilisateurs.models import Utilisateur, Notification, MessageContact


def initialiser_donnees_base_si_vide():
    """
    Si la base de données MySQL est vide après la première migration,
    peuple automatiquement les données initiales d'EauSolidaire en base MySQL
    afin que les tableaux de bord et la carte soient immédiatement alimentés par MySQL.
    """
    if Village.objects.exists() or PointEau.objects.exists():
        return

    toutes_regions = [
        'Kayes', 'Koulikoro', 'Sikasso', 'Ségou', 'Mopti',
        'Tombouctou', 'Gao', 'Kidal', 'Ménaka', 'Taoudénit', 'Bamako'
    ]
    for r_nom in toutes_regions:
        Region.objects.get_or_create(nom=r_nom)

    villages_init = [
        {'n': 'Sadiola', 'c': 'Sadiola', 'ce': 'Kéniéba', 'r': 'Kayes'},
        {'n': 'Siby', 'c': 'Siby', 'ce': 'Kati', 'r': 'Koulikoro'},
        {'n': 'Kadiolo', 'c': 'Kadiolo', 'ce': 'Kadiolo', 'r': 'Sikasso'},
        {'n': 'Markala', 'c': 'Markala', 'ce': 'Ségou', 'r': 'Ségou'},
        {'n': 'Djenné', 'c': 'Djenné', 'ce': 'Djenné', 'r': 'Mopti'},
        {'n': 'Diré', 'c': 'Diré', 'ce': 'Diré', 'r': 'Tombouctou'},
    ]
    villages_map = {}
    for v in villages_init:
        reg, _ = Region.objects.get_or_create(nom=v['r'])
        cer, _ = Cercle.objects.get_or_create(nom=v['ce'], region=reg)
        com, _ = Commune.objects.get_or_create(nom=v['c'], cercle=cer)
        vil, _ = Village.objects.get_or_create(nom=v['n'], commune=com)
        villages_map[v['n']] = vil

    pts_init = [
        {'ref': 'FOR-001', 'n': 'Forage à pompe manuelle du marché', 't': 'Forage', 'v': 'Sadiola', 's': 'Fonctionnel', 'la': 13.85, 'lo': -11.7},
        {'ref': 'PUI-002', 'n': 'Puits à grand diamètre', 't': 'Puits', 'v': 'Siby', 's': 'En panne', 'la': 12.4, 'lo': -8.35},
        {'ref': 'FOR-003', 'n': 'Forage solaire du CSCom', 't': 'Forage', 'v': 'Kadiolo', 's': 'En maintenance', 'la': 10.95, 'lo': -5.75},
        {'ref': 'FOR-004', 'n': 'Mini-adduction d’eau solaire', 't': 'Forage', 'v': 'Markala', 's': 'Fonctionnel', 'la': 13.7, 'lo': -6.07},
        {'ref': 'PUI-005', 'n': 'Puits amélioré de la mosquée', 't': 'Puits', 'v': 'Djenné', 's': 'Hors service', 'la': 13.9, 'lo': -4.55},
        {'ref': 'AUT-006', 'n': 'Borne fontaine', 't': 'Autre', 'v': 'Diré', 's': 'Fonctionnel', 'la': 16.27, 'lo': -3.4},
        {'ref': 'FOR-007', 'n': 'Forage de l’école', 't': 'Forage', 'v': 'Siby', 's': 'Fonctionnel', 'la': None, 'lo': None},
    ]
    pts_map = {}
    for p in pts_init:
        pt = PointEau.objects.create(
            identifiant=p['ref'],
            nom=p['n'],
            type_point=p['t'],
            village=villages_map[p['v']],
            etat_fonctionnement=p['s'],
            latitude=p['la'],
            longitude=p['lo'],
            description=f"{p['n']} situé à {p['v']}",
        )
        HistoriqueEtatPointEau.objects.create(
            point_eau=pt,
            statut=p['s'],
            note='Initialisation base MySQL',
        )
        pts_map[p['ref']] = pt

    # Équipements initiaux associés aux points d'eau
    Equipement.objects.get_or_create(
        reference='EQ-FOR-001',
        defaults={
            'point_eau': pts_map['FOR-001'],
            'nom': 'Pompe India Mark II',
            'type_equipement': 'Pompe manuelle',
            'etat': 'Fonctionnel',
            'description': 'Pompe à motricité humaine installée au marché de Sadiola',
        },
    )
    eq_solaire, _ = Equipement.objects.get_or_create(
        reference='EQ-FOR-003',
        defaults={
            'point_eau': pts_map['FOR-003'],
            'nom': 'Kit Pompe Solaire Lorentz PS2',
            'type_equipement': 'Panneau solaire',
            'etat': 'En maintenance',
            'description': 'Alimentation solaire du forage du CSCom de Kadiolo',
        },
    )

    # Techniciens initiaux
    tech_mamadou, _ = Technicien.objects.get_or_create(
        nom_complet='Mamadou Traoré',
        defaults={
            'specialite': 'Pompes solaires et hydraulique villageoise',
            'telephone': '+223 76 00 00 01',
            'email': 'mamadou.traore@eausolidaire.ml',
            'region_affectation': Region.objects.filter(nom='Sikasso').first(),
            'disponible': True,
        },
    )
    Technicien.objects.get_or_create(
        nom_complet='Awa Coulibaly',
        defaults={
            'specialite': 'Forages à motricité humaine et puits améliorés',
            'telephone': '+223 76 00 00 02',
            'email': 'awa.coulibaly@eausolidaire.ml',
            'region_affectation': Region.objects.filter(nom='Koulikoro').first(),
            'disponible': True,
        },
    )

    # Pannes et interventions initiales
    Panne.objects.create(
        point_eau=pts_map['PUI-002'],
        description='Corde et poulie cassées',
        niveau_gravite='Élevée',
        statut='Nouveau signalement',
        nom_declarant='Resp. Siby',
    )
    panne_2 = Panne.objects.create(
        point_eau=pts_map['FOR-003'],
        equipement=eq_solaire,
        description='Panneau solaire défaillant, pompe à l’arrêt',
        niveau_gravite='Critique',
        statut='En cours de réparation',
        nom_declarant='Resp. Kadiolo',
    )
    Intervention.objects.create(
        panne=panne_2,
        technicien=tech_mamadou,
        statut='En cours de réparation',
        travaux_realises='Diagnostic du contrôleur et remplacement du panneau solaire en cours.',
    )
    Panne.objects.create(
        point_eau=pts_map['PUI-005'],
        description='Margelle effondrée après l’hivernage',
        niveau_gravite='Moyenne',
        statut='En attente d’affectation',
        nom_declarant='Resp. Djenné',
    )

    # Stock initial
    stocks_init = [
        {'n': 'Joint de piston', 'ref': 'P-01', 'q': 12, 'min': 5, 'prix': 2500},
        {'n': 'Clapet de pompe manuelle', 'ref': 'P-02', 'q': 3, 'min': 4, 'prix': 8500},
        {'n': 'Tige inox 3 m', 'ref': 'P-03', 'q': 30, 'min': 10, 'prix': 15000},
    ]
    for s in stocks_init:
        PieceDetachee.objects.get_or_create(
            reference=s['ref'],
            defaults={
                'nom': s['n'],
                'quantite_disponible': s['q'],
                'seuil_alerte': s['min'],
                'prix_unitaire': s['prix'],
            },
        )

    # Notifications initiales
    Notification.objects.create(message='Nouveau signalement : PUI-002')
    Notification.objects.create(message='Stock faible : Clapet de pompe manuelle')


def construire_etat_complet(request):
    """Construit le dictionnaire complet D et U depuis la base de données MySQL."""
    try:
        initialiser_donnees_base_si_vide()
    except Exception:
        pass

    villages = [
        v.to_frontend_dict()
        for v in Village.objects.select_related('commune__cercle__region').all()
    ]
    pts = [
        p.to_frontend_dict()
        for p in PointEau.objects.select_related('village').prefetch_related('historiques_etat').all()
    ]
    pannes = [
        p.to_frontend_dict()
        for p in Panne.objects.select_related('point_eau', 'signale_par').prefetch_related('interventions__technicien').all()
    ]
    stock = [s.to_frontend_dict() for s in PieceDetachee.objects.all()]
    hist = [str(m) for m in MouvementStock.objects.select_related('piece').all()[:30]]
    if not request.user.is_authenticated:
        notifs = []
        messages_contact = []
    elif request.user.frontend_role_code == 'admin':
        notifs = [n.message for n in Notification.objects.filter(lue=False, utilisateur__isnull=True)[:30]]
        messages_contact = [m.to_frontend_dict() for m in MessageContact.objects.all()[:50]]
    else:
        notifs = [n.message for n in Notification.objects.filter(lue=False, utilisateur=request.user)[:20]]
        messages_contact = []
    techs_list = list(Technicien.objects.values_list('nom_complet', flat=True))
    for u_tech in Utilisateur.objects.filter(role='TECHNICIEN', is_active=True):
        disp = u_tech.get_display_name()
        if disp and disp not in techs_list:
            techs_list.append(disp)
    techs = techs_list
    equipements = [e.to_frontend_dict() for e in Equipement.objects.select_related('point_eau').all()]
    users_db = [
        {
            'role': u.frontend_role_code,
            'nom': u.get_display_name(),
            'email': (u.email or '').lower(),
            'tel': u.telephone or '',
            'village': u.village.nom if u.village else '',
        }
        for u in Utilisateur.objects.select_related('village').filter(is_active=True)
        if u.frontend_role_code in ('local', 'tech')
    ]

    user_data = None
    if request.user.is_authenticated:
        village_nom = request.user.village.nom if getattr(request.user, 'village', None) else 'Siby'
        user_data = {
            'id': request.user.id,
            'email': request.user.email,
            'name': request.user.get_display_name(),
            'nom': request.user.get_display_name(),
            'role': request.user.frontend_role_code,
            'role_db': request.user.role,
            'village': village_nom,
        }

    return {
        'D': {
            'villages': villages,
            'pts': pts,
            'pannes': pannes,
            'stock': stock,
            'hist': hist,
            'notifs': notifs,
            'techs': techs,
            'equipements': equipements,
            'users': users_db,
            'messages': messages_contact,
        },
        'U': user_data,
    }


@ensure_csrf_cookie
def accueil(request):
    """Affiche l'interface existante EauSolidaire sans aucune modification visuelle."""
    return render(request, 'suivi/acceuil.html')


def api_state(request):
    """Retourne l'intégralité des données MySQL pour alimenter l'interface et les tableaux de bord."""
    state = construire_etat_complet(request)
    return JsonResponse({'ok': True, **state})
