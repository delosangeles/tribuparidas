from rest_framework import serializers

from .models import News


class NewsSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = News
        fields = [
            "id",
            "title",
            "description",
            "image_desktop",
            "image_mobile",
            "link",
            "published_at",
            "expires_at",
            "order",
            "is_active",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_by_name",
            "created_at",
            "updated_at",
        ]

    def get_created_by_name(self, obj):
        user = obj.created_by

        full_name = f"{user.first_name} {user.last_name}".strip()

        return full_name or user.email