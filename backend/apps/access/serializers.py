from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.blog.models import BlogCategory

from .models import ModuleAccess

User = get_user_model()


class ModuleAccessOutSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = ModuleAccess
        fields = ["module", "can_add", "can_approve", "can_edit", "can_delete", "categories"]

    def get_categories(self, obj):
        return [{"id": c.id, "name": c.name, "slug": c.slug} for c in obj.categories.all()]


class ModuleAccessInSerializer(serializers.Serializer):
    module = serializers.ChoiceField(choices=ModuleAccess.Module.choices)
    can_add = serializers.BooleanField(default=False)
    can_approve = serializers.BooleanField(default=False)
    can_edit = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)
    # Solo para el blog; vacío = todas las categorías.
    categories = serializers.PrimaryKeyRelatedField(queryset=BlogCategory.objects.all(), many=True, required=False)

    def validate(self, attrs):
        if not any(attrs[k] for k in ("can_add", "can_approve", "can_edit", "can_delete")):
            raise serializers.ValidationError("Marca al menos una acción en cada módulo asignado.")
        if attrs["module"] != ModuleAccess.Module.BLOG and attrs.get("categories"):
            raise serializers.ValidationError("Las categorías solo aplican al módulo blog.")
        return attrs


class MadrinaSerializer(serializers.ModelSerializer):
    access = ModuleAccessOutSerializer(source="module_access", many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "is_active", "access"]
