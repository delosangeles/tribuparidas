from rest_framework import permissions


class IsBusinessOwner(permissions.BasePermission):
    """Solo el dueño del emprendimiento puede modificarlo. Lectura: cualquiera autenticado."""

    def has_object_permission(self, request, view, obj):
        business = obj if hasattr(obj, "owner") else obj.business
        if request.method in permissions.SAFE_METHODS:
            return True
        return business.owner_id == request.user.id
