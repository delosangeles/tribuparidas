from rest_framework import serializers

from .models import Category


class SubcategoryMiniSerializer(serializers.ModelSerializer):
    businesses_count = serializers.IntegerField(source="businesses.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "image", "is_active", "businesses_count", "created_at"]


class CategorySerializer(serializers.ModelSerializer):
    businesses_count = serializers.IntegerField(source="businesses.count", read_only=True)
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(parent__isnull=True), allow_null=True, required=False
    )
    parent_name = serializers.CharField(source="parent.name", read_only=True, default=None)
    subcategories = SubcategoryMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "parent",
            "parent_name",
            "subcategories",
            "businesses_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]

    def validate_parent(self, value):
        if not value:
            return value
        if value.parent_id:
            raise serializers.ValidationError("Solo se permiten dos niveles: categoría y subcategoría.")
        if self.instance:
            if value.pk == self.instance.pk:
                raise serializers.ValidationError("Una categoría no puede ser su propia categoría padre.")
            if self.instance.subcategories.exists():
                raise serializers.ValidationError(
                    "Esta categoría ya tiene subcategorías propias; no puede convertirse en subcategoría de otra."
                )
        return value
