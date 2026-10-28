from datetime import date

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.access.services import has_module, module_permission
from apps.core.models import FeatureFlag, log_activity

from .generator import generate
from .logic import month_bounds, week_bounds
from .models import Festejo
from .serializers import FestejoSerializer


def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def is_festejos_module_live():
    """Los festejos pueden estar desplegados pero ocultos hasta la fecha que el
    Super Admin programe en /admin/lanzamiento (FeatureFlag "festejos_module").
    Si el flag no existe todavía (entorno sin migrar) se comporta como activo,
    igual que el blog, para no romper nada por accidente."""
    flag = FeatureFlag.objects.filter(key="festejos_module").first()
    return flag.is_active if flag else True


def range_for(scope, day):
    return month_bounds(day) if scope == "month" else week_bounds(day)


FestejosModulePermission = module_permission(
    "festejos",
    {
        "create": "add",
        "update": "edit",
        "partial_update": "edit",
        "destroy": "delete",
        "approve": "approve",
        "approve_all": "approve",
    },
)


class FestejoViewSet(viewsets.ModelViewSet):
    """/api/festejos/ — las usuarias activas ven los festejos aprobados;
    el equipo admin ve todos y puede aprobar, editar, eliminar y agregar.

    GET ?scope=week|month&date=AAAA-MM-DD&kind=mothers|children|<tipo>
    - week: lunes a domingo de la semana que contiene `date` (hoy por defecto).
    - month: el mes completo de `date`.
    Al consultar se generan (idempotente) los festejos del rango.

    Antes de la fecha de lanzamiento (flag "festejos_module") solo el equipo
    admin los ve; para el resto la lista llega vacía y no se genera nada."""

    serializer_class = FestejoSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [FestejosModulePermission()]

    def get_queryset(self):
        qs = Festejo.objects.select_related("user", "user__member_profile", "child")
        if not has_module(self.request.user, "festejos"):
            if not is_festejos_module_live():
                return qs.none()
            qs = qs.filter(status=Festejo.Status.APPROVED)
        return qs.filter(user__is_active=True, user__is_approved=True)

    def list(self, request, *args, **kwargs):
        day = parse_date(request.query_params.get("date")) or date.today()
        start, end = range_for(request.query_params.get("scope", "week"), day)
        if has_module(request.user, "festejos") or is_festejos_module_live():
            generate(start, end)
        qs = self.get_queryset().filter(event_date__range=(start, end))
        if request.query_params.get("approved") == "1":
            # Vista pública: incluso el equipo admin ve solo lo aprobado (lo mismo que las usuarias).
            qs = qs.filter(status=Festejo.Status.APPROVED)
        kind = request.query_params.get("kind")
        if kind == "mothers":
            qs = qs.filter(kind=Festejo.Kind.MOTHER_BIRTHDAY)
        elif kind == "children":
            qs = qs.exclude(kind=Festejo.Kind.MOTHER_BIRTHDAY)
        elif kind:
            qs = qs.filter(kind=kind)
        return Response({"start": start, "end": end, "results": self.get_serializer(qs, many=True).data})

    def perform_create(self, serializer):
        festejo = serializer.save(is_manual=True)
        log_activity(self.request.user, "festejo_created", f"{self.request.user.email} agregó el festejo «{festejo}».", target=festejo)

    def perform_update(self, serializer):
        festejo = serializer.save()
        log_activity(self.request.user, "festejo_updated", f"{self.request.user.email} editó el festejo «{festejo}».", target=festejo)

    def perform_destroy(self, instance):
        log_activity(self.request.user, "festejo_deleted", f"{self.request.user.email} eliminó el festejo «{instance}».")
        instance.delete()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        festejo = self.get_object()
        festejo.status = Festejo.Status.APPROVED
        festejo.save(update_fields=["status", "updated_at"])
        log_activity(request.user, "festejo_approved", f"{request.user.email} aprobó el festejo «{festejo}».", target=festejo)
        return Response(self.get_serializer(festejo).data)

    @action(detail=False, methods=["post"])
    def approve_all(self, request):
        """Aprueba todos los pendientes de la semana o del mes indicado."""
        day = parse_date(request.data.get("date")) or date.today()
        start, end = range_for(request.data.get("scope"), day)
        count = Festejo.objects.filter(event_date__range=(start, end), status=Festejo.Status.PENDING).update(
            status=Festejo.Status.APPROVED
        )
        log_activity(request.user, "festejo_approved", f"{request.user.email} aprobó {count} festejos ({start} a {end}).")
        return Response({"approved": count}, status=status.HTTP_200_OK)
