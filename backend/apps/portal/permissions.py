from rest_framework import permissions
from rest_framework.exceptions import NotFound, PermissionDenied

from .models import BusinessOwner
from .services import is_portal_module_live, portal_membership


class PortalModuleLive(permissions.BasePermission):
    """Antes del lanzamiento programado nadie (salvo el equipo admin) ve el
    módulo: responde 404 como si no existiera."""

    def has_permission(self, request, view):
        if is_portal_module_live() or (request.user and request.user.is_staff):
            return True
        raise NotFound()


class PortalBusinessMixin:
    """Toda vista del portal cuelga de /portal/businesses/<business_id>/…
    La propiedad se verifica aquí, en el servidor: si la persona no tiene una
    fila BusinessOwner para ESE emprendimiento, responde 404 (no revela si
    existe). `owner_only` excluye a las vendedoras."""

    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]
    owner_only = False  # ni siquiera leer
    write_requires_owner = True  # escribir solo la dueña; las vendedoras leen

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        access = portal_membership(request.user, kwargs.get("business_id"))
        if access is None:
            raise NotFound()
        restricted = self.owner_only or (self.write_requires_owner and request.method not in permissions.SAFE_METHODS)
        if restricted and access.role != BusinessOwner.Role.OWNER:
            raise PermissionDenied("Tu rol de vendedora no permite esta acción.")
        self.access = access
        self.business = access.business

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["business"] = self.business
        return context
