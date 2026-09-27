from django.db.models import Q
from django.utils import timezone

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import BlogCategory, BlogStage, BlogPost
from .serializers import (
    BlogCategorySerializer,
    BlogStageSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostWriteSerializer,
)


class BlogCategoryViewSet(viewsets.ModelViewSet):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAuthenticated]


class BlogStageViewSet(viewsets.ModelViewSet):
    queryset = BlogStage.objects.all()
    serializer_class = BlogStageSerializer
    permission_classes = [IsAuthenticated]

class BlogPostViewSet(viewsets.ModelViewSet):
    queryset = BlogPost.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return BlogPostListSerializer

        if self.action == "retrieve":
            return BlogPostDetailSerializer

        return BlogPostWriteSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        if not self.request.user.is_staff:
            queryset = queryset.filter(
                status=BlogPost.Status.PUBLISHED,
                publication_date__lte=timezone.now()
            )

        search = self.request.query_params.get("search")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(summary__icontains=search) |
                Q(content__icontains=search)
            )

        category = self.request.query_params.get("category")

        if category:
            queryset = queryset.filter(
                category__slug=category
            )

        stage = self.request.query_params.get("stage")

        if stage:
            queryset = queryset.filter(
                stages__slug=stage
            )

        content_type = self.request.query_params.get("content_type")

        if content_type:
            queryset = queryset.filter(
                content_type=content_type
            )

        featured = self.request.query_params.get("featured")

        if featured == "true":
            queryset = queryset.filter(
                featured=True
            )

        return queryset.distinct()