from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Business, BusinessImage
from .permissions import IsBusinessOwner
from .serializers import (
    BusinessDetailSerializer,
    BusinessImageSerializer,
    BusinessListSerializer,
    BusinessWriteSerializer,
)


class BusinessPublicViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/businesses/ y /api/businesses/{slug}/ — solo negocios aprobados."""

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    filterset_fields = ["category__slug", "city", "department"]
    search_fields = ["name", "description", "city"]
    ordering_fields = ["average_rating", "created_at", "name"]

    def get_queryset(self):
        return (
            Business.objects.filter(status=Business.Status.APPROVED)
            .select_related("category")
            .prefetch_related("images")
        )

    def get_serializer_class(self):
        if self.action == "list":
            return BusinessListSerializer
        return BusinessDetailSerializer


class MyBusinessViewSet(viewsets.ModelViewSet):
    """/api/my/businesses/ — CRUD de los emprendimientos del usuario autenticado."""

    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        return (
            Business.objects.filter(owner=self.request.user)
            .select_related("category")
            .prefetch_related("images")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return BusinessWriteSerializer
        return BusinessDetailSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user, status=Business.Status.PENDING)


class MyBusinessImageViewSet(viewsets.ModelViewSet):
    """/api/my/businesses/{business_id}/images/ — galería del emprendimiento propio."""

    serializer_class = BusinessImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "delete", "patch", "head", "options"]

    def get_business(self):
        return get_object_or_404(Business, pk=self.kwargs["business_pk"], owner=self.request.user)

    def get_queryset(self):
        return BusinessImage.objects.filter(business=self.get_business())

    def perform_create(self, serializer):
        serializer.save(business=self.get_business())


class AdminBusinessViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/admin/businesses/ — moderación: listar en cualquier estado, aprobar/rechazar."""

    serializer_class = BusinessDetailSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["status", "category__slug", "city"]
    search_fields = ["name", "owner__email", "city"]
    ordering_fields = ["created_at", "name", "status"]
    queryset = Business.objects.all().select_related("category", "owner")

    @action(detail=True, methods=["patch"])
    def approve(self, request, pk=None):
        business = self.get_object()
        business.status = Business.Status.APPROVED
        business.save(update_fields=["status", "updated_at"])
        return Response(BusinessDetailSerializer(business).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["patch"])
    def reject(self, request, pk=None):
        business = self.get_object()
        business.status = Business.Status.REJECTED
        business.save(update_fields=["status", "updated_at"])
        return Response(BusinessDetailSerializer(business).data, status=status.HTTP_200_OK)
