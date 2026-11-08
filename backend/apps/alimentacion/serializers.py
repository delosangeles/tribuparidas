from django.db import transaction
from rest_framework import serializers

from apps.blog.sanitize import sanitize_blog_html

from .models import (
    AgeRange,
    Allergen,
    FoodItem,
    GuideArticle,
    MealType,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    SafetyContent,
    Status,
)


class CatalogSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        fields = ["id", "name", "slug", "order", "is_active"]


class AgeRangeSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = AgeRange


class AllergenSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = Allergen


class MealTypeSerializer(CatalogSerializer):
    class Meta(CatalogSerializer.Meta):
        model = MealType


class CatalogRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    slug = serializers.CharField()


# ---------- Lectura pública ----------

class GuideListSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuideArticle
        fields = ["id", "slug", "title", "summary", "image", "updated_at"]


class GuideDetailSerializer(GuideListSerializer):
    class Meta(GuideListSerializer.Meta):
        fields = GuideListSerializer.Meta.fields + ["content", "status"]


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeIngredient
        fields = ["name", "quantity"]


class StepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ["text"]


class RecipeListSerializer(serializers.ModelSerializer):
    age_range = CatalogRefSerializer(read_only=True)
    meal_type = CatalogRefSerializer(read_only=True)
    allergens = CatalogRefSerializer(many=True, read_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id", "slug", "title", "summary", "image", "age_range", "meal_type",
            "prep_time_minutes", "allergens", "search_text", "is_favorite", "status",
        ]

    def get_is_favorite(self, obj):
        return obj.id in self.context.get("favorite_ids", ())


class RecipeDetailSerializer(RecipeListSerializer):
    ingredients = IngredientSerializer(many=True, read_only=True)
    steps = StepSerializer(many=True, read_only=True)

    class Meta(RecipeListSerializer.Meta):
        fields = RecipeListSerializer.Meta.fields + ["storage_tip", "ingredients", "steps", "updated_at"]


class FoodItemSerializer(serializers.ModelSerializer):
    age_range = CatalogRefSerializer(read_only=True)
    allergen = CatalogRefSerializer(read_only=True)

    class Meta:
        model = FoodItem
        fields = ["id", "slug", "name", "age_range", "how_to_offer", "is_common_allergen", "allergen", "status"]


class SafetySerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyContent
        fields = ["content", "professional_name", "professional_title", "reviewed_on", "status", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_content(self, value):
        return sanitize_blog_html(value)

    def validate(self, attrs):
        # No se publica sin contenido y sin la firma del profesional que lo redactó.
        current = self.instance
        merged = {f: attrs.get(f, getattr(current, f, "")) for f in ("status", "content", "professional_name")}
        if merged["status"] == Status.PUBLISHED and not (merged["content"].strip() and merged["professional_name"].strip()):
            raise serializers.ValidationError("Para publicar la sección de seguridad hace falta el contenido y el nombre del profesional que la firma.")
        return attrs


# ---------- Escritura (panel admin) ----------

class GuideAdminSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = GuideArticle
        fields = ["id", "slug", "title", "summary", "content", "image", "order", "status", "created_at", "updated_at"]
        read_only_fields = ["image", "created_at", "updated_at"]

    def validate_content(self, value):
        return sanitize_blog_html(value)


class FoodItemAdminSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)

    class Meta:
        model = FoodItem
        fields = [
            "id", "slug", "name", "age_range", "how_to_offer", "is_common_allergen",
            "allergen", "order", "status", "updated_at",
        ]
        read_only_fields = ["updated_at"]


class RecipeAdminSerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(required=False, allow_blank=True)
    ingredients = IngredientSerializer(many=True, required=False)
    steps = StepSerializer(many=True, required=False)
    allergens = serializers.PrimaryKeyRelatedField(many=True, queryset=Allergen.objects.all(), required=False)

    class Meta:
        model = Recipe
        fields = [
            "id", "slug", "title", "summary", "image", "age_range", "meal_type",
            "prep_time_minutes", "allergens", "storage_tip", "ingredients", "steps",
            "order", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["image", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["allergens"] = list(instance.allergens.values_list("id", flat=True))
        return data

    @staticmethod
    def _save_children(recipe, ingredients, steps):
        if ingredients is not None:
            recipe.ingredients.all().delete()
            RecipeIngredient.objects.bulk_create(
                RecipeIngredient(recipe=recipe, order=i, **row) for i, row in enumerate(ingredients)
            )
        if steps is not None:
            recipe.steps.all().delete()
            RecipeStep.objects.bulk_create(RecipeStep(recipe=recipe, order=i, **row) for i, row in enumerate(steps))
        recipe.refresh_search_text()

    @transaction.atomic
    def create(self, validated):
        ingredients = validated.pop("ingredients", None)
        steps = validated.pop("steps", None)
        allergens = validated.pop("allergens", [])
        recipe = Recipe.objects.create(**validated)
        recipe.allergens.set(allergens)
        self._save_children(recipe, ingredients, steps)
        return recipe

    @transaction.atomic
    def update(self, instance, validated):
        ingredients = validated.pop("ingredients", None)
        steps = validated.pop("steps", None)
        allergens = validated.pop("allergens", None)
        for key, value in validated.items():
            setattr(instance, key, value)
        instance.save()
        if allergens is not None:
            instance.allergens.set(allergens)
        self._save_children(instance, ingredients, steps)
        return instance


__all__ = [name for name in dir() if name.endswith("Serializer")] + ["Status"]
