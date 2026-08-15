from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets

from apps.businesses.models import Business

from .models import Product
from .serializers import ProductSerializer


class BusinessProductsPublicView(generics.ListAPIView):
    """GET /api/businesses/{slug}/products/ — productos activos de un negocio aprobado."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "name"]

    def get_queryset(self):
        return Product.objects.filter(
            business__slug=self.kwargs["slug"],
            business__status=Business.Status.APPROVED,
            is_active=True,
        )


class MyBusinessProductsViewSet(viewsets.ModelViewSet):
    """/api/my/businesses/{business_id}/products/ — CRUD de productos del propio negocio."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

    def get_business(self):
        return get_object_or_404(Business, pk=self.kwargs["business_pk"], owner=self.request.user)

    def get_queryset(self):
        return Product.objects.filter(business=self.get_business())

    def perform_create(self, serializer):
        serializer.save(business=self.get_business())


class MyProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """/api/my/products/{id}/ — editar o borrar un producto propio."""

    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(business__owner=self.request.user)
