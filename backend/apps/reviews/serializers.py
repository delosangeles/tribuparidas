from django.utils import timezone
from rest_framework import serializers

from apps.businesses.serializers import BusinessListSerializer

from .models import Favorite, Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    reply = serializers.SerializerMethodField()

    def get_reply(self, obj):
        reply = getattr(obj, "reply", None)
        if reply is None:
            return None
        return {"text": reply.text, "created_at": reply.created_at, "updated_at": reply.updated_at}

    class Meta:
        model = Review
        fields = [
            "id", "business", "user", "user_name", "rating", "comment", "is_active", "reply", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "business", "user", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate(self, attrs):
        request = self.context["request"]
        business = self.context["business"]
        # Se pueden dejar varias opiniones por emprendimiento, pero solo una por día (hora de Bogotá).
        start = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
        if Review.objects.filter(business=business, user=request.user, created_at__gte=start).exists():
            raise serializers.ValidationError("Hoy ya dejaste una opinión para este emprendimiento. Puedes dejar otra mañana.")
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    business = BusinessListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "business", "created_at"]
