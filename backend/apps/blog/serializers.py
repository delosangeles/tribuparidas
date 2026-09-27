from django.contrib.auth import get_user_model

from rest_framework import serializers

from .models import BlogCategory, BlogStage, BlogPost, BlogComment


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
            "stage_names",
            "author_name",
            "content_type",
            "status",
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
        else:
            validated_data["author"] = request.user
            validated_data["status"] = BlogPost.Status.IN_REVIEW

        return super().create(validated_data)


class BlogCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            "id",
            "post",
            "author",
            "author_name",
            "content",
            "created_at",
        ]
        read_only_fields = ["id", "post", "author", "author_name", "created_at"]

    def get_author_name(self, obj):
        return (
            obj.author.get_full_name()
            or obj.author.email
        )


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogComment
        fields = ["content"]
