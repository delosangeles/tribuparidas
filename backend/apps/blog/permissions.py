from rest_framework import permissions

from apps.access.services import can


class BlogPostPermission(permissions.BasePermission):
    """Leer: abierto. Crear: requiere sesión iniciada. Editar y eliminar:
    administradoras o madrinas con esa acción en el blog y solo sobre posts de
    sus categorías."""

    def _needed(self, request):
        return "delete" if request.method == "DELETE" else "edit"

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == "POST":
            return bool(request.user and request.user.is_authenticated)
        return can(request.user, "blog", self._needed(request))

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS or request.method == "POST":
            return True
        return can(request.user, "blog", self._needed(request), category_id=obj.category_id)


class BlogApprovePermission(permissions.BasePermission):
    """Aprobar / rechazar un post en revisión (administradoras o madrinas con
    "aprobar" en el blog, dentro de sus categorías)."""

    def has_permission(self, request, view):
        return can(request.user, "blog", "approve")

    def has_object_permission(self, request, view, obj):
        return can(request.user, "blog", "approve", category_id=obj.category_id)
