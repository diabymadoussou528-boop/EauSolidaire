import json
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST
from .models import Utilisateur, Notification, MessageContact


@require_POST
def api_login(request):
    """Authentification sécurisée par adresse e-mail ou identifiant."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    identifiant = (data.get('u') or data.get('email') or '').strip()
    password = data.get('p') or data.get('password') or ''

    if not identifiant or not password:
        return JsonResponse({'ok': False, 'error': 'Veuillez saisir votre identifiant/e-mail et votre mot de passe.'}, status=400)

    user = authenticate(request, username=identifiant, password=password)
    if user is None:
        # Tentative par username ou nom_complet si l'utilisateur n'a pas saisi l'e-mail exact
        candidate = (
            Utilisateur.objects.filter(email__iexact=identifiant).first()
            or Utilisateur.objects.filter(username__iexact=identifiant).first()
            or Utilisateur.objects.filter(nom_complet__iexact=identifiant).first()
        )
        if candidate:
            user = authenticate(request, username=candidate.email, password=password)

    if user is None:
        return JsonResponse({'ok': False, 'error': 'Identifiants incorrects.'}, status=401)

    if not user.is_active:
        return JsonResponse({'ok': False, 'error': 'Ce compte est désactivé.'}, status=403)

    login(request, user)
    village_nom = user.village.nom if user.village else 'Siby'
    return JsonResponse({
        'ok': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.get_display_name(),
            'role': user.frontend_role_code,
            'role_db': user.role,
            'village': village_nom,
        }
    })


@require_POST
def api_logout(request):
    """Déconnexion et fermeture de la session Django."""
    logout(request)
    return JsonResponse({'ok': True})


@require_POST
def api_clear_notifications(request):
    """Marquer toutes les notifications comme lues."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)
    Notification.objects.filter(lue=False).update(lue=True)
    return JsonResponse({'ok': True})


@require_POST
def api_contact(request):
    """Enregistrement d'un message depuis le formulaire de contact public."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    sujet = (data.get('sj') or data.get('sujet') or 'Information').strip()
    nom = (data.get('nom') or data.get('nom_complet') or '').strip()
    email = (data.get('email') or '').strip()
    msg = (data.get('msg') or data.get('message') or '').strip()

    if not nom or not email or len(msg) < 10:
        return JsonResponse({'ok': False, 'error': 'Veuillez remplir correctement tous les champs.'}, status=400)

    contact = MessageContact.objects.create(
        sujet=sujet[:100],
        nom_complet=nom[:150],
        email=email,
        message=msg[:500],
    )
    Notification.objects.create(message=f"Nouveau message ({contact.sujet}) de {contact.nom_complet}")
    return JsonResponse({'ok': True, 'id': contact.id})


@require_POST
def api_password_reset_request(request):
    """Envoie un e-mail de réinitialisation de mot de passe avec jeton sécurisé Django."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    email = (data.get('email') or '').strip()
    if not email:
        return JsonResponse({'ok': False, 'error': 'Veuillez saisir votre adresse e-mail.'}, status=400)

    user = Utilisateur.objects.filter(email__iexact=email, is_active=True).first()
    if user:
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.check_token(user, default_token_generator.make_token(user)) and default_token_generator.make_token(user)
        reset_link = f"{request.scheme}://{request.get_host()}/?uid={uid}&token={token}#connexion"
        sujet = "Réinitialisation de votre mot de passe – EauSolidaire"
        corps = (
            f"Bonjour {user.get_display_name()},\n\n"
            f"Vous avez demandé la réinitialisation de votre mot de passe sur la plateforme EauSolidaire.\n"
            f"Cliquez sur le lien suivant pour définir un nouveau mot de passe :\n{reset_link}\n\n"
            f"Code UID : {uid}\n"
            f"Jeton de sécurité : {token}\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet e-mail."
        )
        try:
            send_mail(
                sujet,
                corps,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@eausolidaire.ml'),
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            return JsonResponse({'ok': False, 'error': f"Erreur d'envoi SMTP : {e}"}, status=500)

    return JsonResponse({
        'ok': True,
        'message': 'Si cette adresse e-mail correspond à un compte actif, un lien de réinitialisation a été envoyé.',
    })


@require_POST
def api_password_reset_confirm(request):
    """Vérifie le jeton Django et met à jour le mot de passe de l'utilisateur."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    uidb64 = (data.get('uid') or '').strip()
    token = (data.get('token') or '').strip()
    new_password = data.get('password') or ''

    if not uidb64 or not token or len(new_password) < 8:
        return JsonResponse(
            {'ok': False, 'error': 'Jeton invalide ou mot de passe trop court (8 caractères minimum).'},
            status=400,
        )

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Utilisateur.objects.get(pk=uid, is_active=True)
    except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return JsonResponse({'ok': False, 'error': 'Le lien ou jeton de réinitialisation est invalide ou expiré.'}, status=400)

    user.set_password(new_password)
    user.save()
    return JsonResponse({'ok': True, 'message': 'Mot de passe mis à jour avec succès.'})

