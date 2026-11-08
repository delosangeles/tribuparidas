import uuid

from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.access.services import can, has_module
from apps.core.models import log_activity
from apps.core.validators import validate_image_file

from .models import (
    AgeRange,
    Allergen,
    FavoriteRecipe,
    FoodItem,
    GuideArticle,
    MealType,
    Recipe,
    SafetyContent,
    Status,
)
from .permissions import AlimentacionAdminPermission, AlimentacionModuleLive
from .serializers import (
    AgeRangeSerializer,
    AllergenSerializer,
    FoodItemAdminSerializer,
    FoodItemSerializer,
    GuideAdminSerializer,
    GuideDetailSerializer,
    GuideListSerializer,
    MealTypeSerializer,
    RecipeAdminSerializer,
    RecipeDetailSerializer,
    RecipeListSerializer,
    SafetySerializer,
)
from .services import filter_recipes

MODULE = "alimentacion"


def visible(request, qs):
    """Solo lo publicado; el equipo del módulo ve borradores con ?preview=1."""
    if request.query_params.get("preview") == "1" and has_module(request.user, MODULE):
        return qs
    return qs.filter(status=Status.PUBLISHED)


def favorite_ids(user):
    if not user or not user.is_authenticated:
        return set()
    return set(FavoriteRecipe.objects.filter(user=user).values_list("recipe_id", flat=True))


# ---------- Público (solo lectura; favoritos con sesión) ----------

class PublicBase:
    permission_classes = [AlimentacionModuleLive]
    pagination_class = None
    lookup_field = "slug"


class GuideViewSet(PublicBase, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        return visible(self.request, GuideArticle.objects.all())

    def get_serializer_class(self):
        return GuideDetailSerializer if self.action == "retrieve" else GuideListSerializer


class RecipeViewSet(PublicBase, viewsets.ReadOnlyModelViewSet):
    def get_queryset(self):
        qs = Recipe.objects.select_related("age_range", "meal_type").prefetch_related("allergens", "ingredients", "steps")
        return filter_recipes(visible(self.request, qs), self.request.query_params)

    def get_serializer_class(self):
        return RecipeDetailSerializer if self.action == "retrieve" else RecipeListSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["favorite_ids"] = favorite_ids(self.request.user)
        return context


class FoodViewSet(PublicBase, viewsets.ReadOnlyModelViewSet):
    serializer_class = FoodItemSerializer

    def get_queryset(self):
        return visible(self.request, FoodItem.objects.select_related("age_range", "allergen"))


class SafetyView(APIView):
    permission_classes = [AlimentacionModuleLive]

    def get(self, request):
        obj = SafetyContent.get_solo()
        if obj.status != Status.PUBLISHED and not (
            request.query_params.get("preview") == "1" and has_module(request.user, MODULE)
        ):
            return Response({"published": False})
        return Response({"published": True, **SafetySerializer(obj).data})


class CatalogsView(APIView):
    permission_classes = [AlimentacionModuleLive]

    def get(self, request):
        return Response({
            "ages": AgeRangeSerializer(AgeRange.objects.filter(is_active=True), many=True).data,
            "meal_types": MealTypeSerializer(MealType.objects.filter(is_active=True), many=True).data,
            "allergens": AllergenSerializer(Allergen.objects.filter(is_active=True), many=True).data,
        })


class FavoriteListView(APIView):
    permission_classes = [permissions.IsAuthenticated, AlimentacionModuleLive]

    def get(self, request):
        recipes = (
            Recipe.objects.filter(favorites__user=request.user, status=Status.PUBLISHED)
            .select_related("age_range", "meal_type")
            .prefetch_related("allergens")
            .order_by("-favorites__created_at")
        )
        context = {"request": request, "favorite_ids": favorite_ids(request.user)}
        return Response(RecipeListSerializer(recipes, many=True, context=context).data)


class FavoriteToggleView(APIView):
    permission_classes = [permissions.IsAuthenticated, AlimentacionModuleLive]

    def _recipe(self, slug):
        return get_object_or_404(Recipe, slug=slug, status=Status.PUBLISHED)

    def post(self, request, slug):
        FavoriteRecipe.objects.get_or_create(user=request.user, recipe=self._recipe(slug))
        return Response({"is_favorite": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, slug):
        FavoriteRecipe.objects.filter(user=request.user, recipe__slug=slug).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------- Panel de administración ----------

class ImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(validators=[validate_image_file])


class AdminBase(viewsets.ModelViewSet):
    """CRUD del panel. Permisos por módulo (`apps/access`): administradoras
    todo; madrinas solo lo asignado. Publicar exige la acción "aprobar".
    Todo cambio queda en ActivityLog."""

    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    entity = ""  # etiqueta para el historial
    entity_key = ""  # clave de acción: alimentacion_<key>_<verbo>
    name_field = "title"
    has_status = True

    def get_permissions(self):
        return [AlimentacionAdminPermission()]

    def _label(self, obj):
        return f"{self.entity} «{getattr(obj, self.name_field)}»"

    def _log(self, verb, past, obj, target=True):
        log_activity(
            self.request.user,
            f"alimentacion_{self.entity_key}_{verb}",
            f"{self.request.user.email} {past} {self._label(obj)}.",
            target=obj if target else None,
        )

    def _check_publish(self, serializer):
        if self.has_status and serializer.validated_data.get("status") == Status.PUBLISHED:
            if not can(self.request.user, MODULE, "approve"):
                raise PermissionDenied("No tienes permiso para publicar; guárdalo como borrador.")

    def perform_create(self, serializer):
        self._check_publish(serializer)
        obj = serializer.save()
        self._log("created", "creó", obj)

    def perform_update(self, serializer):
        self._check_publish(serializer)
        obj = serializer.save()
        self._log("updated", "editó", obj)

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        label = self._label(obj)
        try:
            obj.delete()
        except ProtectedError:
            return Response(
                {"detail": "No se puede eliminar: está en uso. Desactívalo o cámbialo en las recetas primero."},
                status=status.HTTP_409_CONFLICT,
            )
        log_activity(request.user, f"alimentacion_{self.entity_key}_deleted", f"{request.user.email} eliminó {label}.")
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _set_status(self, new_status, verb, past):
        obj = self.get_object()
        obj.status = new_status
        obj.save()
        self._log(verb, past, obj)
        return Response(self.get_serializer(obj).data)

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        return self._set_status(Status.PUBLISHED, "published", "publicó")

    @action(detail=True, methods=["post"])
    def unpublish(self, request, pk=None):
        return self._set_status(Status.DRAFT, "unpublished", "ocultó")

    @action(detail=False, methods=["post"])
    def reorder(self, request):
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            return Response({"detail": "Envía `ids` como lista de números."}, status=status.HTTP_400_BAD_REQUEST)
        for position, pk in enumerate(ids):
            self.get_queryset().filter(pk=pk).update(order=position)
        log_activity(request.user, f"alimentacion_{self.entity_key}_reordered", f"{request.user.email} reordenó: {self.entity}.")
        return Response({"ok": True})



class ImageActionMixin:
    @action(detail=True, methods=["post", "delete"], parser_classes=[MultiPartParser])
    def image(self, request, pk=None):
        obj = self.get_object()
        if request.method == "DELETE":
            obj.image.delete(save=True)
            self._log("image_removed", "quitó la imagen de", obj)
            return Response(self.get_serializer(obj).data)
        data = ImageUploadSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        file = data.validated_data["image"]
        ext = {"image/png": "png", "image/webp": "webp"}.get(getattr(file, "content_type", ""), "jpg")
        file.name = f"{uuid.uuid4().hex}.{ext}"
        if obj.image:
            obj.image.delete(save=False)
        obj.image = file
        obj.save()
        self._log("image_updated", "cambió la imagen de", obj)
        return Response(self.get_serializer(obj).data)


class RecipeAdminViewSet(ImageActionMixin, AdminBase):
    serializer_class = RecipeAdminSerializer
    entity, entity_key = "la receta", "recipe"

    def get_queryset(self):
        qs = Recipe.objects.select_related("age_range", "meal_type").prefetch_related("allergens", "ingredients", "steps")
        qs = filter_recipes(qs, self.request.query_params)
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class GuideAdminViewSet(ImageActionMixin, AdminBase):
    serializer_class = GuideAdminSerializer
    queryset = GuideArticle.objects.all()
    entity, entity_key = "la guía", "guide"


class FoodAdminViewSet(AdminBase):
    serializer_class = FoodItemAdminSerializer
    queryset = FoodItem.objects.all()
    entity, entity_key, name_field = "el alimento", "food", "name"

    def get_queryset(self):
        return FoodItem.objects.all()


class CatalogAdminBase(AdminBase):
    name_field = "name"
    has_status = False


class AgeAdminViewSet(CatalogAdminBase):
    serializer_class = AgeRangeSerializer
    queryset = AgeRange.objects.all()
    entity, entity_key = "la edad", "age"


class AllergenAdminViewSet(CatalogAdminBase):
    serializer_class = AllergenSerializer
    queryset = Allergen.objects.all()
    entity, entity_key = "el alérgeno", "allergen"


class MealTypeAdminViewSet(CatalogAdminBase):
    serializer_class = MealTypeSerializer
    queryset = MealType.objects.all()
    entity, entity_key = "el tipo de comida", "mealtype"


class SafetyAdminView(APIView):
    """GET/PATCH /api/alimentacion/admin/seguridad/ — la sección fija."""

    permission_classes = [permissions.IsAuthenticated]

    def _check(self, request):
        needed = "view" if request.method == "GET" else "edit"
        ok = has_module(request.user, MODULE) if needed == "view" else can(request.user, MODULE, "edit")
        if not ok:
            raise PermissionDenied("No tienes permiso para esta acción.")

    def get(self, request):
        self._check(request)
        return Response(SafetySerializer(SafetyContent.get_solo()).data)

    def patch(self, request):
        self._check(request)
        obj = SafetyContent.get_solo()
        if request.data.get("status") == Status.PUBLISHED and not can(request.user, MODULE, "approve"):
            raise PermissionDenied("No tienes permiso para publicar; guárdalo como borrador.")
        serializer = SafetySerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_activity(request.user, "alimentacion_safety_updated", f"{request.user.email} editó la sección de seguridad.", target=obj)
        return Response(serializer.data)
