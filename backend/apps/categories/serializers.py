from rest_framework import serializers

from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    businesses_count = serializers.IntegerField(source="businesses.count", read_only=True)

    class Meta:
        model = Category
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "image",
            "is_active",
            "businesses_count",
            "created_at",
        ]
        read_only_fields = ["id", "slug", "created_at"]
