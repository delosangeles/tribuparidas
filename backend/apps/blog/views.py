from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import generics, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import FeatureFlag, log_activity
from apps.access.services import ALL, blog_scope, can, has_module
from apps.core.permissions import IsAdminOrReadOnly

from .models import BlogCategory, BlogStage, BlogPost, BlogComment, BlogCommentLike
from .permissions import BlogApprovePermission, BlogPostPermission
from .serializers import (
    BlogCategorySerializer,
    BlogStageSerializer,
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostWriteSerializer,
    BlogCommentSerializer,
    BlogCommentCreateSerializer,
    BlogCommentUpdateSerializer,
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
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = BlogCategory.objects.all()

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("order", "name")


class BlogStageViewSet(viewsets.ModelViewSet):
    queryset = BlogStage.objects.all()
    serializer_class = BlogStageSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = BlogStage.objects.all()

        is_active = self.request.query_params.get("is_active")

        if is_active == "true":
            queryset = queryset.filter(is_active=True)

        return queryset.order_by("order", "name")


class BlogPostViewSet(viewsets.ModelViewSet):
    """Leer es abierto (sin sesión solo se ven los publicados). Cualquier
    persona registrada puede crear un post — queda en revisión (`IN_REVIEW`)
    salvo que lo cree un admin — pero solo un admin puede editarlo,
    aprobarlo o borrarlo."""

    queryset = BlogPost.objects.all()
    permission_classes = [BlogPostPermission]
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return BlogPostListSerializer

        if self.action == "retrieve":
            return BlogPostDetailSerializer

        return BlogPostWriteSerializer

    def get_queryset(self):
        queryset = BlogPost.objects.all()

        user = self.request.user
        scope = blog_scope(user)  # ALL (administradora), ids de categorías (madrina) o None

        if scope != ALL:
            # Las madrinas, además de lo publicado, ven todo (borradores y en
            # revisión) de las categorías que administran.
            managed = scope if isinstance(scope, set) else set()
            conditions = []

            if is_blog_module_live():
                public = Q(status=BlogPost.Status.PUBLISHED, publication_date__lte=timezone.now())

                # Los blogs privados solo los ve quien tiene sesión.
                if not user.is_authenticated:
                    public &= Q(visibility=BlogPost.Visibility.PUBLIC)

                conditions.append(public)

            if managed:
                conditions.append(Q(category_id__in=managed))

            if not conditions:
                return queryset.none()

            combined = conditions[0]
            for condition in conditions[1:]:
                combined |= condition

            queryset = queryset.filter(combined)

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
        elif not can(self.request.user, "blog", "add", category_id=post.category_id):
            log_activity(
                self.request.user,
                "blog_post_published_open",
                f"{self.request.user.email} publicó en «{post.category.name}» sin aprobación previa: «{post.title}».",
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
        user = self.request.user
        instance = serializer.instance
        was_published = instance.status == BlogPost.Status.PUBLISHED

        if not user.is_staff:
            # Una madrina no puede sacar un post de sus categorías ni publicar sin permiso de aprobar.
            new_category = serializer.validated_data.get("category")
            if new_category and not can(user, "blog", "edit", category_id=new_category.id):
                raise PermissionDenied("No puedes mover el blog a una categoría que no administras.")
            if (
                serializer.validated_data.get("status") == BlogPost.Status.PUBLISHED
                and not was_published
                and not can(user, "blog", "approve", category_id=instance.category_id)
            ):
                raise PermissionDenied("No tienes permiso para aprobar blogs.")

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
        permission_classes=[IsAuthenticated, BlogApprovePermission],
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
        permission_classes=[IsAuthenticated, BlogApprovePermission],
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


def blog_post_for(request, slug):
    """Artículo al que se comenta; antes del lanzamiento solo lo ve el equipo admin."""
    post = get_object_or_404(BlogPost, slug=slug)
    if not has_module(request.user, "blog") and not is_blog_module_live():
        raise Http404
    if post.visibility == BlogPost.Visibility.PRIVATE and not request.user.is_authenticated:
        raise Http404
    return post


def comments_queryset():
    return BlogComment.objects.select_related("author", "post").prefetch_related(
        "likes", "replies__author", "replies__likes"
    )


class BlogPostCommentsView(generics.ListCreateAPIView):
    """GET/POST /api/blog/{slug}/comments/ — leer es abierto; comentar o
    responder requiere sesión (texto y/o una foto). Devuelve los comentarios
    principales (más nuevos primero), cada uno con sus respuestas, reacciones
    y foto. No se modera antes de publicar (a diferencia del blog, no es
    contenido editorial que necesite revisión previa)."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    ordering_fields = ["created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BlogCommentCreateSerializer
        return BlogCommentSerializer

    def get_post(self):
        return blog_post_for(self.request, self.kwargs["slug"])

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == "POST":
            context["post"] = self.get_post()
        return context

    def get_queryset(self):
        return comments_queryset().filter(post=self.get_post(), parent__isnull=True)

    def create(self, request, *args, **kwargs):
        post = self.get_post()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(post=post, author=request.user)
        comment = comments_queryset().get(pk=comment.pk)
        return Response(
            BlogCommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class BlogCommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """/api/blog/{slug}/comments/{id}/ — solo la autora edita su comentario
    (texto y foto); la autora o un admin pueden eliminarlo (con sus respuestas).
    Un admin NO puede editar comentarios ajenos."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        post = blog_post_for(self.request, self.kwargs["slug"])
        return comments_queryset().filter(post=post)

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return BlogCommentUpdateSerializer
        return BlogCommentSerializer

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author_id != request.user.id:
            return Response({"detail": "Solo puedes editar tus propios comentarios."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        comment = self.get_queryset().get(pk=comment.pk)
        return Response(BlogCommentSerializer(comment, context={"request": request}).data)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        is_author = comment.author_id == request.user.id
        if not (is_author or can(request.user, "blog", "delete", category_id=comment.post.category_id)):
            return Response({"detail": "No puedes eliminar este comentario."}, status=status.HTTP_403_FORBIDDEN)
        if not is_author:
            log_activity(
                request.user,
                "blog_comment_deleted",
                f"{request.user.email} eliminó un comentario de {comment.author.email} en «{comment.post.title}».",
                target=comment.post,
            )
        if comment.image:
            comment.image.delete(save=False)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BlogCommentLikeView(APIView):
    """POST /api/blog/{slug}/comments/{id}/like/ — pone o quita el "me gusta"
    de quien tiene sesión. Devuelve el estado final."""

    permission_classes = [IsAuthenticated]

    def post(self, request, slug, pk):
        post = blog_post_for(request, slug)
        comment = get_object_or_404(BlogComment, pk=pk, post=post)
        like, created = BlogCommentLike.objects.get_or_create(comment=comment, user=request.user)
        if not created:
            like.delete()
        return Response({"liked": created, "like_count": comment.likes.count()})
