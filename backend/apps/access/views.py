from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import log_activity
from apps.core.permissions import IsSuperAdmin

from .models import ModuleAccess
from .serializers import MadrinaSerializer, ModuleAccessInSerializer

User = get_user_model()


def madrinas_queryset():
    return User.objects.filter(module_access__isnull=False).distinct().prefetch_related("module_access__categories").order_by("first_name", "email")


class MadrinaListView(APIView):
    """GET /api/admin/madrinas/ — solo Super Admin: quiénes tienen acceso a módulos y con qué acciones."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response(MadrinaSerializer(madrinas_queryset(), many=True).data)


class MadrinaDetailView(APIView):
    """PUT /api/admin/madrinas/<user_id>/ — define (reemplaza) los accesos de la usuaria.
    DELETE — le quita todos. Solo Super Admin. Las administradoras (is_staff) ya
    tienen acceso total y no se pueden convertir en madrinas."""

    permission_classes = [IsSuperAdmin]

    def put(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if user.is_staff or user.is_superuser:
            raise serializers.ValidationError({"detail": "Esa persona ya es administradora y tiene acceso a todo."})
        if not user.is_active:
            raise serializers.ValidationError({"detail": "La cuenta debe estar activa para asignarle acceso."})

        entries = ModuleAccessInSerializer(data=request.data.get("access", []), many=True)
        entries.is_valid(raise_exception=True)
        modules = [e["module"] for e in entries.validated_data]
        if not modules or len(modules) != len(set(modules)):
            raise serializers.ValidationError({"access": "Asigna al menos un módulo, sin repetirlo."})

        with transaction.atomic():
            user.module_access.exclude(module__in=modules).delete()
            for e in entries.validated_data:
                access, _ = ModuleAccess.objects.update_or_create(
                    user=user,
                    module=e["module"],
                    defaults={k: e[k] for k in ("can_add", "can_approve", "can_edit", "can_delete")},
                )
                access.categories.set(e.get("categories", []))
        log_activity(request.user, "madrina_updated", f"{request.user.email} asignó accesos a {user.email}: {', '.join(modules)}.", target=user)
        return Response(MadrinaSerializer(madrinas_queryset().get(pk=user.pk)).data)

    def delete(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        user.module_access.all().delete()
        log_activity(request.user, "madrina_removed", f"{request.user.email} quitó los accesos de {user.email}.", target=user)
        return Response(status=status.HTTP_204_NO_CONTENT)
