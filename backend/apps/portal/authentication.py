from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication

# Una cuenta "solo portal" únicamente puede usar estas rutas; el resto del
# sitio (blog, festejos, noticias, favoritos, preguntas, opiniones…) es de
# las usuarias de la página. Se aplica aquí, en el servidor, para no depender
# solo de que el frontend oculte los enlaces.
PORTAL_ACCOUNT_PREFIXES = ("/api/auth/", "/api/me/", "/api/portal/", "/api/feature-flags/", "/api/analytics/")
PORTAL_ACCOUNT_READ_PREFIXES = ("/api/businesses/", "/api/categories/")


class PortalAwareJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, _token = result
        if getattr(user, "account_type", "member") == "portal":
            path = request.path
            allowed = path.startswith(PORTAL_ACCOUNT_PREFIXES) or (
                request.method in SAFE_METHODS and path.startswith(PORTAL_ACCOUNT_READ_PREFIXES)
            )
            if not allowed:
                raise PermissionDenied("Tu cuenta es solo de portal. Pide a un administrador pasar a usuaria de la página.")
        return result
