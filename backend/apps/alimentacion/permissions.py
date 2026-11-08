from rest_framework import permissions
from rest_framework.exceptions import NotFound

from apps.access.services import has_module, module_permission

from .services import is_alimentacion_module_live


class AlimentacionModuleLive(permissions.BasePermission):
    """Antes del lanzamiento nadie (salvo el equipo del módulo) ve nada: la
    API responde 404 como si no existiera."""

    def has_permission(self, request, view):
        if is_alimentacion_module_live() or has_module(request.user, "alimentacion"):
            return True
        raise NotFound()


AlimentacionAdminPermission = module_permission(
    "alimentacion",
    {
        "list": "view",
        "retrieve": "view",
        "create": "add",
        "update": "edit",
        "partial_update": "edit",
        "destroy": "delete",
        "publish": "approve",
        "unpublish": "approve",
        "reorder": "edit",
        "image": "edit",
    },
)
