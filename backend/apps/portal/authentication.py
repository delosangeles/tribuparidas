from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import SAFE_METHODS
from rest_framework_simplejwt.authentication import JWTAuthentication

# Una cuenta "solo portal" únicamente puede usar estas rutas; el resto del
# sitio (blog, festejos, noticias, favoritos, preguntas, opiniones…) es de
# las usuarias de la página. Se aplica aquí, en el servidor, para no depender
# solo de que el frontend oculte los enlaces.
PORTAL_ACCOUNT_PREFIXES = ("/api/auth/", "/api/me/", "/api/portal/", "/api/feature-flags/", "/api/analytics/")
PORTAL_ACCOUNT_READ_PREFIXES = ("/api/businesses/", "/api/categories/")


# Cuenta activa pero SIN aprobar (aún no se confirma que está en el grupo de WhatsApp):
# solo puede iniciar sesión, ver/editar su perfil y pedir acceso. En lo público
# (lectura) se trata como visitante, así que no ve noticias privadas.
UNAPPROVED_PREFIXES = ("/api/auth/", "/api/me/", "/api/feature-flags/", "/api/analytics/", "/api/site-settings/")
UNAPPROVED_PUBLIC_READ_PREFIXES = ("/api/businesses/", "/api/categories/", "/api/blog/", "/api/news/")


class PortalAwareJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        user, _token = result
        if not user.is_staff and not getattr(user, "is_approved", True):
            path = request.path
            if path.startswith(UNAPPROVED_PREFIXES):
                return result
            if request.method in SAFE_METHODS and path.startswith(UNAPPROVED_PUBLIC_READ_PREFIXES):
                return None
            raise PermissionDenied(
                "Debes pertenecer al grupo de WhatsApp de la tribu. Solicita tu acceso y te aprobaremos pronto.",
                code="not_approved",
            )
        if getattr(user, "account_type", "member") == "portal":
            path = request.path
            allowed = path.startswith(PORTAL_ACCOUNT_PREFIXES) or (
                request.method in SAFE_METHODS and path.startswith(PORTAL_ACCOUNT_READ_PREFIXES)
            )
            if not allowed:
                raise PermissionDenied("Tu cuenta es solo de portal. Pide a un administrador pasar a usuaria de la página.")
        return result
