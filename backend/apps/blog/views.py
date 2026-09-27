from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.models import FeatureFlag, log_activity
from apps.core.permissions import IsAdminOrCreateOnly, IsAdminOrReadOnly

from .models import BlogCategory, BlogStage, BlogPost, BlogComment
from .serializers import (
    BlogCategorySerializer,
    BlogStageSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostWriteSerializer,
    BlogCommentSerializer,
    BlogCommentCreateSerializer,
)


def is_blog_module_live():
    """El blog puede estar desplegado en producción pero oculto hasta la
    fecha que el Super Admin programe en /admin/lanzamiento (FeatureFlag
    "blog_module"). Si el flag no existe todavía (ej. antes de migrar en un
    entorno viejo) se comporta como si ya estuviera activo, para no romper
    nada por accidente."""

    flag = FeatureFlag.objects.filter(key="blog_module").first()
    return flag.is_active if flag else True


class BlogCategoryViewSet(viewsets.ModelViewSet):
    queryset = BlogCategory.objects.all()
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = BlogCategory.objects.all()

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("order", "name")


class BlogStageViewSet(viewsets.ModelViewSet):
    queryset = BlogStage.objects.all()
    serializer_class = BlogStageSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = BlogStage.objects.all()

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("order", "name")


class BlogPostViewSet(viewsets.ModelViewSet):
    """Cualquier persona autenticada puede crear un post — queda en revisión
    (`IN_REVIEW`) salvo que lo cree un admin — pero solo un admin puede
    editarlo, aprobarlo o borrarlo."""

    queryset = BlogPost.objects.all()
    permission_classes = [IsAuthenticated, IsAdminOrCreateOnly]
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
            if not is_blog_module_live():
                return queryset.none()

            queryset = queryset.filter(
                status=BlogPost.Status.PUBLISHED,
                publication_date__lte=timezone.now()
            )

        status_param = self.request.query_params.get("status")

        if status_param:
            queryset = queryset.filter(status=status_param)

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

        if self.action == "list":
            # `annotate` + `distinct` puede perder el ordering por defecto
            # del modelo (Django avisa con UnorderedObjectListWarning al
            # paginar); se reafirma explícitamente.
            queryset = queryset.annotate(comments_count=Count("comments")).order_by(
                "-publication_date", "-created_at"
            )

        return queryset.distinct()

    def perform_create(self, serializer):
        post = serializer.save()

        if post.status == BlogPost.Status.IN_REVIEW:
            log_activity(
                self.request.user,
                "blog_post_submitted",
                f"{self.request.user.email} envió a revisión el blog «{post.title}».",
                target=post,
            )
        else:
            log_activity(
                self.request.user,
                "blog_post_created",
                f"{self.request.user.email} creó el blog «{post.title}».",
                target=post,
            )

    def perform_update(self, serializer):
        was_published = serializer.instance.status == BlogPost.Status.PUBLISHED
        post = serializer.save()

        if not was_published and post.status == BlogPost.Status.PUBLISHED:
            log_activity(
                self.request.user,
                "blog_post_approved",
                f"{self.request.user.email} aprobó y publicó el blog «{post.title}».",
                target=post,
            )
        else:
            log_activity(
                self.request.user,
                "blog_post_updated",
                f"{self.request.user.email} editó el blog «{post.title}».",
                target=post,
            )

    def perform_destroy(self, instance):
        title = instance.title
        actor = self.request.user
        instance.delete()
        log_activity(actor, "blog_post_deleted", f"{actor.email} eliminó el blog «{title}».")

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, permissions.IsAdminUser],
    )
    def approve(self, request, slug=None):
        """POST /api/blog/{slug}/approve/ — publica un post en revisión."""

        post = self.get_object()
        post.status = BlogPost.Status.PUBLISHED

        if not post.publication_date:
            post.publication_date = timezone.now()

        post.save(update_fields=["status", "publication_date"])

        log_activity(
            request.user,
            "blog_post_approved",
            f"{request.user.email} aprobó y publicó el blog «{post.title}».",
            target=post,
        )

        serializer = BlogPostDetailSerializer(post, context=self.get_serializer_context())

        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, permissions.IsAdminUser],
    )
    def reject(self, request, slug=None):
        """POST /api/blog/{slug}/reject/ — devuelve un post en revisión a
        borrador (no lo publica ni lo borra; sale de la cola de revisión)."""

        post = self.get_object()
        post.status = BlogPost.Status.DRAFT
        post.save(update_fields=["status"])

        log_activity(
            request.user,
            "blog_post_rejected",
            f"{request.user.email} rechazó el blog «{post.title}» (vuelve a borrador).",
            target=post,
        )

        serializer = BlogPostDetailSerializer(post, context=self.get_serializer_context())

        return Response(serializer.data)


class BlogPostCommentsView(generics.ListCreateAPIView):
    """GET/POST /api/blog/{slug}/comments/ — cualquier autenticado puede
    comentar; no se modera (a diferencia del blog, no es contenido editorial
    que necesite revisión previa)."""

    permission_classes = [IsAuthenticated]
    ordering_fields = ["created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BlogCommentCreateSerializer
        return BlogCommentSerializer

    def get_post(self):
        post = get_object_or_404(BlogPost, slug=self.kwargs["slug"])

        if not self.request.user.is_staff and not is_blog_module_live():
            raise Http404

        return post

    def get_queryset(self):
        return BlogComment.objects.filter(post=self.get_post()).select_related("author")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=self.get_post(), author=request.user)
        return Response(BlogCommentSerializer(comment).data, status=status.HTTP_201_CREATED)