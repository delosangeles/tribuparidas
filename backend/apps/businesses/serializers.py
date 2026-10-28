from rest_framework import serializers

from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer

from .models import Business, BusinessImage


class BusinessImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessImage
        fields = ["id", "business", "image", "caption", "order", "created_at"]
        read_only_fields = ["id", "business", "created_at"]


class BusinessListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "slug",
            "logo",
            "cover_image",
            "category",
            "city",
            "department",
            "average_rating",
            "status",
            "home_delivery",
            "tribe_benefit",
            "benefit_type",
            "is_mama_tribu",
            "tribe_recommended",
            "created_at",
        ]


class BusinessDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    images = BusinessImageSerializer(many=True, read_only=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    portal_benefit = serializers.SerializerMethodField()
    faqs = serializers.SerializerMethodField()

    def get_portal_benefit(self, obj):
        # Solo se publica el Beneficio Tribu aprobado y vigente (módulo portal).
        from apps.portal.serializers import PublicBenefitSerializer
        from apps.portal.services import bogota_today, is_portal_module_live

        if not is_portal_module_live():
            return None
        benefit = getattr(obj, "benefit", None)
        if benefit is None or not benefit.is_valid_on(bogota_today()):
            return None
        return PublicBenefitSerializer(benefit).data

    def get_faqs(self, obj):
        from apps.portal.serializers import PublicFAQSerializer
        from apps.portal.services import is_portal_module_live

        if not is_portal_module_live():
            return []
        return PublicFAQSerializer(obj.faqs.all(), many=True).data

    class Meta:
        model = Business
        fields = [
            "id",
            "owner",
            "name",
            "slug",
            "logo",
            "cover_image",
            "description",
            "category",
            "city",
            "department",
            "address",
            "whatsapp",
            "instagram",
            "facebook",
            "website",
            "opening_hours",
            "status",
            "average_rating",
            "home_delivery",
            "tribe_benefit",
            "benefit_type",
            "benefit_detail",
            "is_mama_tribu",
            "responsible_name",
            "tribe_recommended",
            "images",
            "portal_benefit",
            "faqs",
            "created_at",
            "updated_at",
        ]


class BusinessWriteSerializer(serializers.ModelSerializer):
    """Usado por el dueño para crear/editar su emprendimiento.

    `status` y `owner` nunca los decide el cliente: se fuerzan en la vista.
    """

    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_active=True))

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "logo",
            "cover_image",
            "description",
            "category",
            "city",
            "department",
            "address",
            "whatsapp",
            "instagram",
            "facebook",
            "website",
            "opening_hours",
            "status",
            "average_rating",
            "home_delivery",
            "tribe_benefit",
            "benefit_type",
            "benefit_detail",
            "is_mama_tribu",
            "responsible_name",
            "tribe_recommended",
            "slug",
        ]
        read_only_fields = ["id", "status", "average_rating", "slug"]

    def validate(self, attrs):
        benefit_type = attrs.get("benefit_type", getattr(self.instance, "benefit_type", ""))
        tribe_benefit = attrs.get("tribe_benefit", getattr(self.instance, "tribe_benefit", False))
        if benefit_type and not tribe_benefit:
            raise serializers.ValidationError(
                {"benefit_type": "Solo aplica si 'Beneficio Tribu' está activado."}
            )
        return attrs

    def to_representation(self, instance):
        return BusinessDetailSerializer(instance, context=self.context).data


class AdminBusinessWriteSerializer(BusinessWriteSerializer):
    """Igual que BusinessWriteSerializer, pero permite al admin crear/editar
    emprendimientos de cualquier usuario y decidir el estado directamente."""

    class Meta(BusinessWriteSerializer.Meta):
        read_only_fields = ["id", "average_rating", "slug"]
