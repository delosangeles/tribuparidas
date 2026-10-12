from django.contrib.auth import get_user_model

from rest_framework import serializers

from django.utils import timezone

from apps.access.services import can
from apps.core.validators import validate_image_file

from .models import OPEN_CATEGORY_SLUG, BlogCategory, BlogStage, BlogPost, BlogComment


class BlogCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "order",
        ]


class BlogStageSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogStage
        fields = [
            "id",
            "name",
            "slug",
            "is_active",
            "order",
        ]


class BlogPostListSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    category_slug = serializers.CharField(source="category.slug", read_only=True)

    author_name = serializers.SerializerMethodField()

    stage_names = serializers.SerializerMethodField()

    comments_count = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "main_image",
            "category",
            "category_name",
            "category_slug",
            "stage_names",
            "author_name",
            "content_type",
            "status",
            "visibility",
            "publication_date",
            "featured",
            "reading_time",
            "comments_count",
        ]

    def get_author_name(self, obj):
        return (
            obj.author.get_full_name()
            or obj.author.email
        )

    def get_stage_names(self, obj):
        return list(
            obj.stages.values_list("name", flat=True)
        )


class BlogPostDetailSerializer(serializers.ModelSerializer):

    category_name = serializers.CharField(
        source="category.name",
        read_only=True
    )

    category_slug = serializers.CharField(
        source="category.slug",
        read_only=True
    )

    author_name = serializers.SerializerMethodField()

    stages_detail = BlogStageSerializer(
        source="stages",
        many=True,
        read_only=True
    )

    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "summary",
            "content",
            "main_image",
            "category",
            "category_name",
            "category_slug",
            "stages_detail",
            "author",
            "author_name",
            "content_type",
            "publication_date",
            "updated_at",
            "status",
            "visibility",
            "featured",
            "reading_time",
            "sources",
            "seo_title",
            "seo_description",
        ]

    def get_author_name(self, obj):
        return (
            obj.author.get_full_name()
            or obj.author.email
        )


class BlogPostWriteSerializer(serializers.ModelSerializer):
    # Solo un admin puede elegir el autor o el estado real de la publicación;
    # a un usuario normal se le fuerzan ambos en create() sin importar lo que
    # haya enviado (ver más abajo).
    author = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),
        required=False,
    )
    # Obligatorio al crear: quien escribe debe elegir público o privado.
    visibility = serializers.ChoiceField(choices=BlogPost.Visibility.choices)

    class Meta:
        model = BlogPost
        fields = [
            "title",
            "slug",
            "summary",
            "content",
            "main_image",
            "category",
            "stages",
            "author",
            "content_type",
            "publication_date",
            "status",
            "visibility",
            "featured",
            "reading_time",
            "sources",
            "seo_title",
            "seo_description",
        ]

    def create(self, validated_data):
        request = self.context["request"]

        if request.user.is_staff:
            validated_data.setdefault("author", request.user)
        elif can(request.user, "blog", "add", category_id=validated_data["category"].id):
            # Madrina con "agregar" en esta categoría: publica sin revisión, siempre a su nombre.
            validated_data["author"] = request.user
            validated_data["featured"] = False
        else:
            validated_data["author"] = request.user
            validated_data["featured"] = False
            if validated_data["category"].slug == OPEN_CATEGORY_SLUG:
                # "Desahogos": se publica al instante, sin aprobación.
                validated_data["status"] = BlogPost.Status.PUBLISHED
                validated_data["publication_date"] = timezone.now()
            else:
                validated_data["status"] = BlogPost.Status.IN_REVIEW

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context["request"]
        if not request.user.is_staff:
            # Solo las administradoras cambian la autoría y destacan blogs.
            validated_data.pop("author", None)
            validated_data.pop("featured", None)
        return super().update(instance, validated_data)


def _absolute(request, image):
    if not image:
        return None
    return request.build_absolute_uri(image.url) if request else image.url


class BlogCommentSerializer(serializers.ModelSerializer):
    """Comentario con su foto, reacciones y respuestas (un solo nivel).

    Las vistas deben precargar `likes` y `replies__author/likes` para evitar
    consultas repetidas (ver BlogPostCommentsView.get_queryset)."""

    author_name = serializers.SerializerMethodField()
    author_photo = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            "id",
            "post",
            "author",
            "author_name",
            "author_photo",
            "parent",
            "content",
            "image",
            "like_count",
            "liked_by_me",
            "replies",
            "can_delete",
            "edited_at",
            "created_at",
        ]
        read_only_fields = fields

    def get_author_name(self, obj):
        return (
            obj.author.get_full_name()
            or obj.author.email
        )

    def get_author_photo(self, obj):
        # La foto de la madre es pública (se ve junto a sus comentarios).
        return _absolute(self.context.get("request"), obj.author.photo)

    def get_image(self, obj):
        return _absolute(self.context.get("request"), obj.image)

    def get_like_count(self, obj):
        return len(obj.likes.all())

    def get_liked_by_me(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        return any(like.user_id == user.id for like in obj.likes.all())

    def get_can_delete(self, obj):
        # La autora, o quien modera el blog (administradoras / madrinas de esa categoría).
        user = getattr(self.context.get("request"), "user", None)
        if not user or not user.is_authenticated:
            return False
        return obj.author_id == user.id or can(user, "blog", "delete", category_id=obj.post.category_id)

    def get_replies(self, obj):
        if obj.parent_id:
            return []
        replies = sorted(obj.replies.all(), key=lambda reply: reply.created_at)
        return BlogCommentSerializer(replies, many=True, context=self.context).data


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    """Crear un comentario o una respuesta, con foto opcional. Debe traer texto
    o foto. Responder a una respuesta cuelga del comentario principal."""

    content = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    image = serializers.ImageField(required=False, allow_null=True, validators=[validate_image_file])
    parent = serializers.PrimaryKeyRelatedField(queryset=BlogComment.objects.all(), required=False, allow_null=True)

    class Meta:
        model = BlogComment
        fields = ["content", "image", "parent"]

    def validate_parent(self, parent):
        if parent is None:
            return None
        if parent.post_id != self.context["post"].id:
            raise serializers.ValidationError("Ese comentario no pertenece a este artículo.")
        return parent.parent if parent.parent_id else parent

    def validate(self, attrs):
        if not (attrs.get("content") or "").strip() and not attrs.get("image"):
            raise serializers.ValidationError({"content": "Escribe algo o agrega una foto."})
        attrs["content"] = (attrs.get("content") or "").strip()
        return attrs


class BlogCommentUpdateSerializer(serializers.ModelSerializer):
    """Editar el propio comentario: texto y foto (cambiarla o quitarla)."""

    content = serializers.CharField(required=False, allow_blank=True, max_length=2000)
    image = serializers.ImageField(required=False, allow_null=True, validators=[validate_image_file])
    remove_image = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = BlogComment
        fields = ["content", "image", "remove_image"]

    def validate(self, attrs):
        content = (attrs.get("content", self.instance.content) or "").strip()
        has_image = bool(attrs.get("image")) or (bool(self.instance.image) and not attrs.get("remove_image"))
        if not content and not has_image:
            raise serializers.ValidationError({"content": "Escribe algo o deja la foto."})
        attrs["content"] = content
        return attrs

    def update(self, instance, validated_data):
        remove = validated_data.pop("remove_image", False)
        if (remove or validated_data.get("image")) and instance.image:
            instance.image.delete(save=False)
        if remove and "image" not in validated_data:
            instance.image = None
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.edited_at = timezone.now()
        instance.save()
        return instance
