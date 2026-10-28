from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.businesses.models import Business, BusinessImage
from apps.categories.models import Category
from apps.reviews.models import Review
from apps.users.models import User

from .models import (
    BusinessBenefit,
    BusinessChangeLog,
    BusinessFAQ,
    BusinessOwner,
    MemberNotice,
)


class PortalBusinessSerializer(serializers.ModelSerializer):
    """Campos que la dueña puede editar. Estado, calificación, banderas de
    "recomendado" y el beneficio antiguo no se tocan desde el portal."""

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_active=True))
    category_name = serializers.CharField(source="category.name", read_only=True)
    public_path = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id", "name", "slug", "logo", "description", "category", "category_name", "city", "department",
            "address", "whatsapp", "instagram", "facebook", "website", "opening_hours", "home_delivery",
            "responsible_name", "status", "average_rating", "public_path",
        ]
        read_only_fields = ["id", "slug", "status", "average_rating"]

    def get_public_path(self, obj):
        return f"/emprendimientos/{obj.slug}"


class PortalImageSerializer(serializers.ModelSerializer):
    is_main = serializers.SerializerMethodField()

    class Meta:
        model = BusinessImage
        fields = ["id", "image", "caption", "order", "is_main", "created_at"]
        read_only_fields = ["id", "order", "created_at"]

    def get_is_main(self, obj):
        first = BusinessImage.objects.filter(business_id=obj.business_id).first()  # la principal es la primera del orden
        return first is not None and first.pk == obj.pk


class PortalReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    reply = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = ["id", "user_name", "rating", "comment", "reply", "created_at"]

    def get_reply(self, obj):
        reply = getattr(obj, "reply", None)
        return None if reply is None else {"text": reply.text, "updated_at": reply.updated_at}


class ReplySerializer(serializers.Serializer):
    text = serializers.CharField(max_length=1000)

    def validate_text(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Escribe una respuesta.")
        return value


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessFAQ
        fields = ["id", "question", "answer", "order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class PublicFAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessFAQ
        fields = ["id", "question", "answer"]


class BenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessBenefit
        fields = ["id", "percentage", "conditions", "valid_from", "valid_until", "status", "reviewed_at", "updated_at"]
        read_only_fields = ["id", "status", "reviewed_at", "updated_at"]

    def validate_percentage(self, value):
        if not 1 <= value <= 100:
            raise serializers.ValidationError("El porcentaje debe estar entre 1 y 100.")
        return value

    def validate(self, attrs):
        start = attrs.get("valid_from", getattr(self.instance, "valid_from", None))
        end = attrs.get("valid_until", getattr(self.instance, "valid_until", None))
        if start and end and end < start:
            raise serializers.ValidationError({"valid_until": "La fecha final no puede ser anterior a la inicial."})
        return attrs


class PublicBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessBenefit
        fields = ["percentage", "conditions", "valid_from", "valid_until"]


class AdminBenefitSerializer(BenefitSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)
    business_id = serializers.IntegerField(read_only=True)

    class Meta(BenefitSerializer.Meta):
        fields = BenefitSerializer.Meta.fields + ["business_id", "business_name"]


class ChangeLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.get_full_name", read_only=True, default="")

    class Meta:
        model = BusinessChangeLog
        fields = ["id", "entity", "action", "changes", "actor_name", "created_at"]


class MemberRowSerializer(serializers.ModelSerializer):
    """Lo único que ve el emprendimiento de una usuaria: nombre, teléfono y
    correo (con su consentimiento). Nunca la cédula."""

    last_activity = serializers.DateTimeField(read_only=True)
    redemption_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "whatsapp", "email", "last_activity", "redemption_count"]


class BusinessOwnerSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    account_type = serializers.CharField(source="user.account_type", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = BusinessOwner
        fields = ["id", "user", "user_name", "user_email", "account_type", "business", "business_name", "role", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_business(self, business):
        if business.status != Business.Status.APPROVED:
            raise serializers.ValidationError("Solo se asigna a emprendimientos aprobados.")
        return business

    def validate_user(self, user):
        if not user.is_active:
            raise serializers.ValidationError("La cuenta debe estar activa (aprobada).")
        return user


class MemberNoticeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberNotice
        fields = ["id", "message", "is_read", "created_at"]


class PortalRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    business_name = serializers.CharField(max_length=150, write_only=True, help_text="Emprendimiento al que representa.")

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "whatsapp", "business_name"]
        extra_kwargs = {"whatsapp": {"required": True}, "email": {"validators": []}}

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value
