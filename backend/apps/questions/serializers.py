from rest_framework import serializers

from .models import Answer, Question


class AnswerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Answer
        fields = ["id", "question", "user", "user_name", "answer", "is_active", "created_at"]
        read_only_fields = ["id", "question", "user", "created_at"]


class AnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ["answer"]


class QuestionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    answer = AnswerSerializer(read_only=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "business",
            "business_name",
            "user",
            "user_name",
            "question",
            "answer",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "business", "user", "created_at"]


class QuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["question"]
