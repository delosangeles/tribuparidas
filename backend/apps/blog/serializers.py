from rest_framework import serializers

from .models import BlogCategory, BlogStage, BlogPost


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
            "publication_date",
            "featured",
            "reading_time",
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

        # Usuario normal: siempre se asigna él mismo
        if not request.user.is_staff:
            validated_data["author"] = request.user

        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context["request"]

        # Usuario normal: no puede cambiar el autor
        if not request.user.is_staff:
            validated_data["author"] = instance.author

        return super().update(
            instance,
            validated_data
        )