from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.businesses.models import Business

from .models import Favorite, Review
from .serializers import FavoriteSerializer, ReviewCreateSerializer, ReviewSerializer


class BusinessReviewsView(generics.ListCreateAPIView):
    """/api/businesses/{business_id}/reviews/ — requiere sesión (sitio privado; 1 por usuario)."""

    ordering_fields = ["created_at", "rating"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ReviewCreateSerializer
        return ReviewSerializer

    def get_business(self):
        return get_object_or_404(Business, pk=self.kwargs["business_id"])

    def get_queryset(self):
        return Review.objects.filter(business=self.get_business(), is_active=True).select_related("user")

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["business"] = self.get_business()
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(business=self.get_business(), user=request.user)
        return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class MyFavoritesListView(generics.ListAPIView):
    """GET /api/my/favorites/"""

    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("business", "business__category")


class FavoriteToggleView(APIView):
    """POST/DELETE /api/businesses/{business_id}/favorite/"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, business_id):
        business = get_object_or_404(Business, pk=business_id, status=Business.Status.APPROVED)
        favorite, created = Favorite.objects.get_or_create(user=request.user, business=business)
        return Response(
            FavoriteSerializer(favorite).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def delete(self, request, business_id):
        deleted, _ = Favorite.objects.filter(user=request.user, business_id=business_id).delete()
        if not deleted:
            return Response({"detail": "No tenías este emprendimiento en favoritos."}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminReviewViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """/api/admin/reviews/ — moderación: ocultar/reactivar opiniones."""

    queryset = Review.objects.all().select_related("business", "user")
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_active", "business", "rating"]
    search_fields = ["comment", "business__name", "user__email"]
    ordering_fields = ["created_at", "rating"]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response(status=204)
