from rest_framework import serializers

from apps.businesses.serializers import BusinessListSerializer

from .models import Favorite, Review


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Review
        fields = ["id", "business", "user", "user_name", "rating", "comment", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "business", "user", "created_at", "updated_at"]


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def validate(self, attrs):
        request = self.context["request"]
        business = self.context["business"]
        if Review.objects.filter(business=business, user=request.user).exists():
            raise serializers.ValidationError("Ya dejaste una opinión para este emprendimiento.")
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    business = BusinessListSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ["id", "business", "created_at"]
