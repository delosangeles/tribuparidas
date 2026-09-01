from rest_framework import permissions, viewsets

from apps.core.models import log_activity
from apps.core.permissions import IsAdminOrReadOnly

from .models import Category
from .serializers import CategorySerializer


class CategoryViewSet(viewsets.ModelViewSet):
    """GET /api/categories/ requiere sesión (sitio privado); crear/editar/borrar requiere admin.

    Por defecto solo devuelve categorías principales (sin padre), con sus
    subcategorías anidadas. Usa ?parent=<id> para listar las subcategorías
    de una categoría puntual, o ?all=1 para traer ambos niveles sin filtrar.
    """

    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    lookup_field = "slug"
    filterset_fields = {"is_active": ["exact"], "parent": ["exact", "isnull"]}
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        qs = Category.objects.all().select_related("parent").prefetch_related("subcategories")
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        if self.action == "list" and not self.request.query_params.get("all") and "parent" not in self.request.query_params:
            qs = qs.filter(parent__isnull=True)
        return qs

    def perform_create(self, serializer):
        category = serializer.save()
        kind = "subcategoría" if category.parent_id else "categoría"
        log_activity(
            self.request.user,
            "category_created",
            f"{self.request.user.email} creó la {kind} «{category.name}».",
            target=category,
        )

    def perform_update(self, serializer):
        category = serializer.save()
        log_activity(
            self.request.user, "category_updated", f"{self.request.user.email} editó la categoría «{category.name}».", target=category
        )

    def perform_destroy(self, instance):
        name = instance.name
        actor = self.request.user
        instance.delete()
        log_activity(actor, "category_deleted", f"{actor.email} eliminó la categoría «{name}».")
