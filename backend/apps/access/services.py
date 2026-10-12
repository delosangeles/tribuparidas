"""Permisos por módulo para madrinas (administradoras de información específica).

Regla central: una usuaria con `is_staff` (administradora actual) conserva
acceso total, tal como hoy. Una madrina (sin is_staff) solo puede lo que
tenga en `ModuleAccess`, y en el blog solo dentro de sus categorías.
"""
from rest_framework import permissions

ACTIONS = ("add", "approve", "edit", "delete")
ACTION_LABELS = {"add": "Agregar", "approve": "Aprobar", "edit": "Editar", "delete": "Eliminar"}

ALL = "all"  # alcance sin restricción de categorías


def get_access(user, module):
    """ModuleAccess de la usuaria para ese módulo (o None). Se cachea por usuaria."""
    if not user or not user.is_authenticated:
        return None
    cache = user.__dict__.setdefault("_module_access_cache", {})
    if module not in cache:
        cache[module] = user.module_access.filter(module=module).prefetch_related("categories").first()
    return cache[module]


def has_module(user, module):
    """¿Puede entrar a la administración de ese módulo? (cualquier acción)."""
    if not user or not user.is_authenticated:
        return False
    return user.is_staff or get_access(user, module) is not None


def blog_scope(user):
    """Categorías del blog que puede administrar: ALL, un set de ids, o None si no tiene acceso."""
    if not user or not user.is_authenticated:
        return None
    if user.is_staff:
        return ALL
    access = get_access(user, "blog")
    if access is None:
        return None
    ids = {c.id for c in access.categories.all()}
    return ids or ALL


def can(user, module, action, category_id=None):
    """¿Puede hacer `action` en `module`? En el blog, si se indica la categoría,
    también debe estar dentro de su alcance."""
    if not user or not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    access = get_access(user, module)
    if access is None or not getattr(access, f"can_{action}", False):
        return False
    if module == "blog" and category_id is not None:
        scope = blog_scope(user)
        return scope == ALL or category_id in scope
    return True


def module_access_payload(user):
    """Resumen para el frontend (menú y botones). None para administradoras: tienen todo."""
    if user.is_staff:
        return None
    payload = {}
    for access in user.module_access.prefetch_related("categories"):
        payload[access.module] = {
            **{action: getattr(access, f"can_{action}") for action in ACTIONS},
            "categories": [c.slug for c in access.categories.all()] or None,  # None = todas
        }
    return payload


class ModuleActionPermission(permissions.BasePermission):
    """Permiso DRF por módulo. `action_map` traduce la acción de la vista a
    la acción de permiso ("add", "approve", "edit", "delete", o "view" = tener
    cualquier acceso). Una acción puede aceptar varias (lista)."""

    module = None
    action_map = {}

    def has_permission(self, request, view):
        required = self.action_map.get(getattr(view, "action", None))
        if required is None:
            return False
        if request.user and request.user.is_staff:
            return True
        required = [required] if isinstance(required, str) else required
        for needed in required:
            if needed == "view":
                if has_module(request.user, self.module):
                    return True
            elif can(request.user, self.module, needed):
                return True
        return False


def module_permission(module, action_map):
    return type(f"{module.capitalize()}ActionPermission", (ModuleActionPermission,), {"module": module, "action_map": action_map})
