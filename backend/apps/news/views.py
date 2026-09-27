from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.core.permissions import IsAdminOrReadOnly

from .models import News
from .serializers import NewsSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

class NewsViewSet(ModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    filter_backends = [
        SearchFilter,
        DjangoFilterBackend,
        OrderingFilter,
    ]

    search_fields = ["title", "description"]
    filterset_fields = ["is_active"]
    ordering_fields = [
        "order",
        "published_at",
        "expires_at",
        "created_at",
    ]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def active(self, request):
        now = timezone.now()

        news = News.objects.filter(
            is_active=True,
            published_at__lte=now,
            expires_at__gte=now,
        ).order_by("order", "-published_at")[:5]

        serializer = self.get_serializer(news, many=True)

        return Response(serializer.data)