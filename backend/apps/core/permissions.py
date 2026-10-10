from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Cualquiera puede leer; solo el dueño del objeto puede escribir.

    Espera que el objeto tenga un atributo `owner`. Para modelos donde el
    dueño se determina indirectamente (ej. un Product a través de su
    Business), la vista debe sobreescribir has_object_permission.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        owner = getattr(obj, "owner", None)
        return owner == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """Cualquiera puede leer; solo un usuario staff puede escribir."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsAdminOrCreateOnly(permissions.BasePermission):
    """Cualquiera puede leer (sitio abierto); crear requiere sesión iniciada;
    solo un staff puede editar o borrar. Pensado para contenido tipo blog:
    cualquier persona registrada envía un borrador a revisión, solo un admin
    lo aprueba, edita o elimina."""

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        authenticated = bool(request.user and request.user.is_authenticated)
        if request.method == "POST":
            return authenticated
        return authenticated and request.user.is_staff


class IsSuperAdmin(permissions.BasePermission):
    """Solo el/los Super Admin (is_superuser=True) — ej. para decidir quién
    más es Administrador."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
