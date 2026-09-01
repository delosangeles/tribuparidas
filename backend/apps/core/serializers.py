from rest_framework import serializers

from .models import ActivityLog, PageView


class ActivityLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True, default=None)
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True, default=None)
    target_type = serializers.CharField(source="content_type.model", read_only=True, default=None)

    class Meta:
        model = ActivityLog
        fields = [
            "id",
            "actor_email",
            "actor_name",
            "action",
            "description",
            "target_type",
            "object_id",
            "created_at",
        ]


class PageViewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PageView
        fields = ["session_id", "path"]
