import json
import random
import re
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.http import require_POST
from localisation.models import Village
from techniciens.models import Technicien
from .models import Utilisateur, Notification, MessageContact


def _normalize_phone(val):
    return re.sub(r'\s+', '', val or '')


@require_POST
def api_login(request):
    """Authentification sécurisée par adresse e-mail, téléphone ou identifiant."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    identifiant = (data.get('ident') or data.get('u') or data.get('email') or '').strip()
    password = data.get('mdp') or data.get('p') or data.get('password') or ''
    expected_role = (data.get('role') or '').strip()

    if not identifiant or not password:
        return JsonResponse(
            {'ok': False, 'error': 'Veuillez saisir votre identifiant/e-mail et votre mot de passe.'},
            status=400,
        )

    # Initialisation automatique du compte superutilisateur diabymadoussou528@gmail.com lors de la première connexion admin
    if identifiant.lower() in ('admin', 'diabymadoussou528@gmail.com'):
        admin_exists = Utilisateur.objects.filter(email__iexact='diabymadoussou528@gmail.com').exists()
        if not admin_exists and len(password) >= 8:
            Utilisateur.objects.create_superuser(
                email='diabymadoussou528@gmail.com',
                password=password,
                username='admin',
                nom_complet='Administrateur',
                role='ADMIN',
            )

    user = authenticate(request, username=identifiant, password=password)
    if user is None:
        # Tentative par email, username, nom_complet ou numéro de téléphone (sans espaces)
        candidate = (
            Utilisateur.objects.filter(email__iexact=identifiant).first()
            or Utilisateur.objects.filter(username__iexact=identifiant).first()
            or Utilisateur.objects.filter(nom_complet__iexact=identifiant).first()
        )
        if candidate is None:
            norm_id = _normalize_phone(identifiant)
            if norm_id:
                for u_cand in Utilisateur.objects.exclude(telephone=''):
                    if _normalize_phone(u_cand.telephone) == norm_id:
                        candidate = u_cand
                        break
        if candidate:
            user = authenticate(request, username=candidate.email, password=password)
            if user is None and candidate.frontend_role_code == 'admin':
                user = authenticate(request, username=candidate.email, password=password.strip())
                if user is None:
                    user = authenticate(request, username=candidate.email, password=password.strip().lower())

    if user is None:
        return JsonResponse({'ok': False, 'error': 'Identifiant ou mot de passe incorrect.'}, status=401)

    if not user.is_active:
        return JsonResponse({'ok': False, 'error': 'Ce compte est désactivé.'}, status=403)

    if expected_role and user.frontend_role_code != expected_role:
        return JsonResponse({'ok': False, 'error': 'Identifiant ou mot de passe incorrect.'}, status=401)

    login(request, user)
    village_nom = user.village.nom if user.village else ('Siby' if user.frontend_role_code == 'local' else '')
    display_name = user.get_display_name()
    return JsonResponse({
        'ok': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': display_name,
            'nom': display_name,
            'tel': user.telephone or '',
            'role': user.frontend_role_code,
            'role_db': user.role,
            'village': village_nom,
        }
    })


@require_POST
def api_register(request):
    """Inscription d'un nouveau compte Responsable local ou Technicien en base MySQL."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    role_code = (data.get('role') or 'local').strip()
    nom = (data.get('nom') or '').strip()
    email = (data.get('email') or '').strip().lower()
    tel = (data.get('tel') or '').strip()
    password = data.get('password') or data.get('npw') or ''
    village_nom = (data.get('village') or data.get('vil') or '').strip()
    specialite = (data.get('spe') or data.get('specialite') or '').strip()

    if role_code not in ('local', 'tech'):
        return JsonResponse(
            {'ok': False, 'error': 'Les comptes administrateur ne se créent pas ici.'},
            status=400,
        )

    if not nom or not email or not tel or len(password) < 8:
        return JsonResponse(
            {'ok': False, 'error': 'Corrigez les champs en rouge.'},
            status=400,
        )

    if Utilisateur.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {'ok': False, 'error': 'Un compte existe déjà avec cette adresse e-mail.'},
            status=400,
        )

    base_username = email.split('@')[0][:120] or 'user'
    username = base_username
    suffix = 1
    while Utilisateur.objects.filter(username__iexact=username).exists():
        username = f"{base_username}_{suffix}"
        suffix += 1

    village_obj = None
    if role_code == 'local' and village_nom:
        try:
            from suivi.views import initialiser_donnees_base_si_vide
            initialiser_donnees_base_si_vide()
        except Exception:
            pass
        village_obj = Village.objects.filter(nom__iexact=village_nom).first()

    db_role = 'TECHNICIEN' if role_code == 'tech' else 'AGENT_LOCAL'

    parts = nom.split(' ', 1)
    first_name = parts[0][:150]
    last_name = parts[1][:150] if len(parts) > 1 else ''

    user = Utilisateur(
        username=username,
        email=email,
        nom_complet=nom[:150],
        first_name=first_name,
        last_name=last_name,
        telephone=tel[:30],
        role=db_role,
        village=village_obj,
        is_active=True,
    )
    user.set_password(password)
    user.save()

    if role_code == 'tech':
        Technicien.objects.update_or_create(
            nom_complet=nom[:150],
            defaults={
                'utilisateur': user,
                'telephone': tel[:30],
                'email': email,
                'specialite': specialite or 'Pompes manuelles',
                'disponible': True,
            },
        )

    role_label = 'Technicien' if role_code == 'tech' else 'Responsable local'
    Notification.objects.create(utilisateur=None, message=f"Nouveau compte : {user.nom_complet} ({role_label})")
    Notification.objects.create(utilisateur=user, message=f"Bienvenue {user.nom_complet} ({role_label})")

    village_phrase = f" pour le village de {village_nom}" if role_code == 'local' and village_nom else ''
    html_corps = (
        f"<div style='font-family:Manrope,Segoe UI,sans-serif;max-width:520px;border:1px solid #d9e3ea;border-radius:14px;overflow:hidden;color:#1b3148'>"
        f"<div style='background:#e9f0f4;padding:12px 16px;font-size:13px;color:#51677d'><b>EauSolidaire</b> · Confirmation de création de compte</div>"
        f"<div style='padding:18px 16px;font-size:14px;line-height:1.6'>"
        f"<p>Bonjour <b>{first_name}</b>,</p>"
        f"<p>Votre compte <b>{role_label}</b> a bien été créé{village_phrase}. "
        f"Vous pouvez dès maintenant vous connecter avec votre adresse e-mail et le mot de passe que vous avez choisi.</p>"
        f"<p>Pour votre sécurité, ce message ne contient jamais votre mot de passe.</p>"
        f"<p>L’équipe EauSolidaire</p>"
        f"</div></div>"
    )
    email_sent = False
    try:
        send_mail(
            'Votre compte EauSolidaire est créé',
            (
                f"Bonjour {first_name},\n\n"
                f"Votre compte {role_label} a bien été créé{village_phrase}. "
                f"Vous pouvez dès maintenant vous connecter avec votre adresse e-mail et le mot de passe que vous avez choisi.\n\n"
                f"Pour votre sécurité, ce message ne contient jamais votre mot de passe.\n\n"
                f"L’équipe EauSolidaire"
            ),
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'EauSolidaire <diabymadoussou528@gmail.com>'),
            [email],
            html_message=html_corps,
            fail_silently=False,
        )
        email_sent = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
    except Exception:
        pass

    return JsonResponse({
        'ok': True,
        'email_sent': email_sent,
        'user': {
            'id': user.id,
            'role': role_code,
            'nom': user.nom_complet,
            'name': user.nom_complet,
            'email': user.email,
            'tel': user.telephone,
            'village': village_nom if role_code == 'local' else '',
            'spe': specialite if role_code == 'tech' else '',
        },
    })


@require_POST
def api_logout(request):
    """Déconnexion et fermeture de la session Django."""
    logout(request)
    return JsonResponse({'ok': True})


@require_POST
def api_clear_notifications(request):
    """Marquer uniquement les notifications du compte connecté comme lues."""
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'error': 'Authentification requise.'}, status=401)
    if request.user.frontend_role_code == 'admin':
        Notification.objects.filter(lue=False, utilisateur__isnull=True).update(lue=True)
    else:
        Notification.objects.filter(lue=False, utilisateur=request.user).update(lue=True)
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
    Notification.objects.create(utilisateur=None, message=f"Nouveau message ({contact.sujet}) de {contact.nom_complet}")
    try:
        dest_email = getattr(settings, 'EMAIL_HOST_USER', '') or 'diabymadoussou528@gmail.com'
        send_mail(
            f"[EauSolidaire Contact] {contact.sujet} – {contact.nom_complet}",
            f"De : {contact.nom_complet} <{contact.email}>\nSujet : {contact.sujet}\n\n{contact.message}",
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'EauSolidaire <diabymadoussou528@gmail.com>'),
            [dest_email],
            fail_silently=True,
        )
    except Exception:
        pass
    return JsonResponse({'ok': True, 'id': contact.id, 'message_obj': contact.to_frontend_dict()})


@require_POST
def api_contact_statut(request):
    """Marquer un message de contact comme traité ou non traité (Administrateur uniquement)."""
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    msg_id = data.get('id')
    contact = MessageContact.objects.filter(id=msg_id).first()
    if not contact:
        return JsonResponse({'ok': False, 'error': 'Message introuvable.'}, status=404)
    contact.traite = bool(data.get('traite', True))
    contact.save()
    return JsonResponse({'ok': True, 'message_obj': contact.to_frontend_dict()})


@require_POST
def api_contact_delete(request):
    """Supprimer un message de contact (Administrateur uniquement)."""
    if not request.user.is_authenticated or request.user.frontend_role_code != 'admin':
        return JsonResponse({'ok': False, 'error': 'Permission refusée.'}, status=403)
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST
    msg_id = data.get('id')
    contact = MessageContact.objects.filter(id=msg_id).first()
    if not contact:
        return JsonResponse({'ok': False, 'error': 'Message introuvable.'}, status=404)
    contact.delete()
    return JsonResponse({'ok': True})


@require_POST
def api_password_reset_request(request):
    """Envoie un code à 6 chiffres et un lien de réinitialisation de mot de passe."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    email = (data.get('email') or '').strip().lower()
    mode = (data.get('mode') or '').strip()
    if not email:
        return JsonResponse({'ok': False, 'error': 'Veuillez saisir votre adresse e-mail.'}, status=400)

    user = Utilisateur.objects.filter(email__iexact=email, is_active=True).first()
    if mode == 'otp':
        if not user:
            return JsonResponse(
                {
                    'ok': False,
                    'error': 'Aucun compte avec cette adresse.',
                },
                status=404,
            )

    otp_code = None
    email_sent = False
    if user:
        otp_code = str(data.get('code') or random.randint(100000, 999999))
        cache.set(f"es_reset_otp_{user.email.lower()}", otp_code, timeout=900)
        request.session[f"es_reset_otp_{user.email.lower()}"] = otp_code

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{request.scheme}://{request.get_host()}/?uid={uid}&token={token}#connexion"
        sujet = "Réinitialisation de votre mot de passe – EauSolidaire"
        corps = (
            f"Bonjour {user.get_display_name()},\n\n"
            f"Votre code EauSolidaire : {otp_code}\n\n"
            f"Vous pouvez également utiliser le lien suivant :\n{reset_link}\n\n"
            f"Code UID : {uid}\n"
            f"Jeton de sécurité : {token}\n\n"
            f"Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet e-mail."
        )
        html_corps = (
            f"<div style='font-family:Manrope,Segoe UI,sans-serif;max-width:520px;border:1px solid #d9e3ea;border-radius:14px;overflow:hidden;color:#1b3148'>"
            f"<div style='background:#e9f0f4;padding:12px 16px;font-size:13px;color:#51677d'><b>EauSolidaire</b> · Code de vérification</div>"
            f"<div style='padding:18px 16px;font-size:14px;line-height:1.6'>"
            f"<p>Bonjour <b>{user.get_display_name()}</b>,</p>"
            f"<p>Votre code EauSolidaire : <b style='font-size:22px;letter-spacing:4px'>{otp_code}</b></p>"
            f"<p style='color:#51677d;font-size:13px'>Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet e-mail.</p>"
            f"</div></div>"
        )
        try:
            send_mail(
                sujet,
                corps,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'EauSolidaire <diabymadoussou528@gmail.com>'),
                [user.email],
                html_message=html_corps,
                fail_silently=False,
            )
            email_sent = bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))
        except Exception as e:
            if mode != 'otp':
                return JsonResponse({'ok': False, 'error': f"Erreur d'envoi SMTP : {e}"}, status=500)

    return JsonResponse({
        'ok': True,
        'code': otp_code,
        'email_sent': email_sent,
        'message': 'Si cette adresse e-mail correspond à un compte actif, un code de réinitialisation a été envoyé.',
    })


@require_POST
def api_password_reset_confirm(request):
    """Vérifie le code à 6 chiffres (ou jeton Django) et met à jour le mot de passe en base MySQL."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()
    uidb64 = (data.get('uid') or '').strip()
    token = (data.get('token') or '').strip()
    new_password = data.get('password') or data.get('npw') or ''

    if len(new_password) < 8:
        return JsonResponse(
            {'ok': False, 'error': 'Jeton invalide ou mot de passe trop court (8 caractères minimum).'},
            status=400,
        )

    # Flux 1 : Code OTP à 6 chiffres (#motdepasse étapes 1 -> 2 -> 3)
    if email and code:
        user = Utilisateur.objects.filter(email__iexact=email, is_active=True).first()
        if not user:
            return JsonResponse({'ok': False, 'error': 'Compte introuvable.'}, status=404)
        expected_code = (
            cache.get(f"es_reset_otp_{email}")
            or request.session.get(f"es_reset_otp_{email}")
        )
        if expected_code and str(expected_code) != str(code):
            return JsonResponse({'ok': False, 'error': 'Code incorrect, réessayez.'}, status=400)
        user.set_password(new_password)
        user.save()
        cache.delete(f"es_reset_otp_{email}")
        request.session.pop(f"es_reset_otp_{email}", None)
        return JsonResponse({'ok': True, 'message': 'Mot de passe mis à jour avec succès.'})

    # Flux 2 : UID + Token Django classique
    if not uidb64 or not token:
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


