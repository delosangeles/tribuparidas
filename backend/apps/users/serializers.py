import secrets

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Notification

User = get_user_model()


def user_role(user):
    if user.is_superuser:
        return "super_admin"
    if user.is_staff:
        return "admin"
    return "user"


class UserSerializer(serializers.ModelSerializer):
    is_entrepreneur = serializers.BooleanField(read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "whatsapp",
            "is_staff",
            "is_superuser",
            "role",
            "is_entrepreneur",
            "created_at",
        ]
        read_only_fields = ["id", "email", "is_staff", "is_superuser", "created_at"]

    def get_role(self, obj):
        return user_role(obj)


class MeUpdateSerializer(serializers.ModelSerializer):
    # El WhatsApp no se puede autoeditar: es lo que usa el equipo admin para
    # confirmar que la persona pertenece al grupo de la tribu.
    class Meta:
        model = User
        fields = ["first_name", "last_name"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual no es correcta.")
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "whatsapp"]
        extra_kwargs = {"whatsapp": {"required": True}}

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value

    def create(self, validated_data):
        # Queda inactiva hasta que un admin confirme que pertenece a la tribu.
        user = User.objects.create_user(**validated_data, is_active=False)
        Notification.objects.create(
            type=Notification.Type.NEW_REGISTRATION,
            related_user=user,
            message=f"{user.get_full_name()} ({user.email}) se registró y espera aprobación.",
        )
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login con email. Además de los tokens, devuelve los datos del usuario
    para que el frontend no tenga que hacer una segunda petición a /me/."""

    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class AdminUserSerializer(serializers.ModelSerializer):
    is_entrepreneur = serializers.BooleanField(read_only=True)
    businesses_count = serializers.IntegerField(source="businesses.count", read_only=True)
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "whatsapp",
            "is_active",
            "is_staff",
            "is_superuser",
            "role",
            "is_entrepreneur",
            "businesses_count",
            "created_at",
        ]
        # is_staff se cambia solo vía la acción set_role (Super Admin); acá queda de solo lectura.
        read_only_fields = ["id", "email", "is_staff", "is_superuser", "created_at"]

    def get_role(self, obj):
        return user_role(obj)


class AdminUserCreateSerializer(serializers.ModelSerializer):
    # is_superuser nunca se otorga desde acá — eso sigue siendo manual, fuera de la API.
    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "whatsapp", "is_staff"]

    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value

    def create(self, validated_data):
        new_password = secrets.token_urlsafe(9)
        user = User.objects.create_user(**validated_data, is_active=True, password=new_password)
        user.generated_password = new_password
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data["email"].lower().strip()
        user = User.objects.filter(email=email).first()
        if user:
            Notification.objects.create(
                type=Notification.Type.PASSWORD_RESET_REQUEST,
                related_user=user,
                message=f"{user.get_full_name()} ({user.email}) olvidó su contraseña y necesita que se la reseteen.",
            )
        # Siempre "exitoso" aunque el email no exista, para no revelar qué
        # correos están registrados.


class NotificationSerializer(serializers.ModelSerializer):
    related_user_email = serializers.CharField(source="related_user.email", read_only=True, default=None)

    class Meta:
        model = Notification
        fields = ["id", "type", "message", "related_user", "related_user_email", "is_read", "created_at"]
        read_only_fields = ["id", "type", "message", "related_user", "related_user_email", "created_at"]
