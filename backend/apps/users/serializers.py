import secrets
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Child, MemberProfile, Notification, Pregnancy

User = get_user_model()


def user_role(user):
    if user.is_superuser:
        return "super_admin"
    if user.is_staff:
        return "admin"
    return "user"


MIN_BIRTH_YEAR = 1930


def validate_not_future(value):
    if value > timezone.localdate():
        raise serializers.ValidationError("La fecha no puede ser futura.")
    if value.year < MIN_BIRTH_YEAR:
        raise serializers.ValidationError("La fecha no es válida.")
    return value


class ChildSerializer(serializers.ModelSerializer):
    """Nombre y fecha de nacimiento obligatorios (a diferencia de la base de
    datos, que los admite vacíos para datos importados incompletos)."""

    id = serializers.IntegerField(required=False)
    name = serializers.CharField(max_length=150)
    birth_date = serializers.DateField(validators=[validate_not_future])

    class Meta:
        model = Child
        fields = ["id", "name", "birth_date"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre es obligatorio.")
        return value


class PregnancySerializer(serializers.ModelSerializer):
    due_date = serializers.DateField()

    class Meta:
        model = Pregnancy
        fields = ["due_date"]

    def validate_due_date(self, value):
        today = timezone.localdate()
        if value < today - timedelta(days=30) or value > today + timedelta(days=330):
            raise serializers.ValidationError("La fecha probable de parto no es válida.")
        return value


class MemberProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemberProfile
        exclude = ["id", "user"]


def sync_festejos_data(user, data):
    """Aplica birth_date / children / pregnancy de un payload validado.
    `children` reemplaza la lista completa (con id actualiza, sin id crea,
    los que no vienen se eliminan); `pregnancy: null` quita el embarazo."""
    if "birth_date" in data:
        user.birth_date = data["birth_date"]
        user.save(update_fields=["birth_date"])

    if "children" in data:
        keep_ids = []
        for item in data["children"]:
            child = user.children.filter(pk=item["id"]).first() if item.get("id") else None
            if child:
                child.name, child.birth_date = item["name"], item["birth_date"]
                child.save()
            else:
                child = Child.objects.create(user=user, name=item["name"], birth_date=item["birth_date"])
            keep_ids.append(child.pk)
        user.children.exclude(pk__in=keep_ids).delete()

    if "pregnancy" in data:
        pregnancy = data["pregnancy"]
        if pregnancy is None:
            Pregnancy.objects.filter(user=user).delete()
        else:
            Pregnancy.objects.update_or_create(user=user, defaults={"due_date": pregnancy["due_date"]})


FESTEJOS_FIELDS = ("birth_date", "children", "pregnancy")


def missing_festejos_data(user):
    """Qué le falta a la usuaria para los festejos (lista legible)."""
    missing = []
    if not user.birth_date:
        missing.append("fecha de cumpleaños")
    for child in user.children.all():
        if not child.name or not child.birth_date:
            missing.append(f"datos de hijo/a ({child.name or 'sin nombre'})")
    return missing


class UserSerializer(serializers.ModelSerializer):
    is_entrepreneur = serializers.BooleanField(read_only=True)
    role = serializers.SerializerMethodField()
    children = ChildSerializer(many=True, read_only=True)
    pregnancy = PregnancySerializer(read_only=True)
    missing_festejos_data = serializers.SerializerMethodField()

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
            "birth_date",
            "children",
            "pregnancy",
            "missing_festejos_data",
            "created_at",
        ]
        read_only_fields = ["id", "email", "is_staff", "is_superuser", "created_at"]

    def get_role(self, obj):
        return user_role(obj)

    def get_missing_festejos_data(self, obj):
        return missing_festejos_data(obj)


class MeUpdateSerializer(serializers.ModelSerializer):
    # El WhatsApp no se puede autoeditar: es lo que usa el equipo admin para
    # confirmar que la persona pertenece al grupo de la tribu.
    birth_date = serializers.DateField(required=False, validators=[validate_not_future])
    children = ChildSerializer(many=True, required=False)
    pregnancy = PregnancySerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "birth_date", "children", "pregnancy"]

    @transaction.atomic
    def update(self, instance, validated_data):
        extra = {k: validated_data.pop(k) for k in FESTEJOS_FIELDS if k in validated_data}
        instance = super().update(instance, validated_data)
        sync_festejos_data(instance, extra)
        return instance


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



# Ventana de lanzamiento: 24h desde que abre el sitio (2026-09-01 7:00pm
# Colombia) donde el registro queda activo de una vez, sin esperar
# aprobación manual — para no generar cuello de botella la noche del
# lanzamiento. Después de esta ventana, vuelve a quedar pendiente.
OPEN_REGISTRATION_START = datetime(2026, 9, 1, 19, 0, 0, tzinfo=dt_timezone(timedelta(hours=-5)))
OPEN_REGISTRATION_END = OPEN_REGISTRATION_START + timedelta(hours=24)


def is_open_registration_window():
    return OPEN_REGISTRATION_START <= timezone.now() <= OPEN_REGISTRATION_END


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    birth_date = serializers.DateField(validators=[validate_not_future])
    children = ChildSerializer(many=True, required=False)
    pregnancy = PregnancySerializer(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "whatsapp", "birth_date", "children", "pregnancy"]
        extra_kwargs = {"whatsapp": {"required": True}, "email": {"validators": []}}

    def validate_email(self, value):
        value = value.lower().strip()
        existing = User.objects.filter(email=value).first()
        # Una cuenta precargada desde el Excel (pendiente de registrarse) se
        # "reclama" registrándose con ese correo; cualquier otra ya existe.
        if existing and existing.registration_status != "pending_registration":
            raise serializers.ValidationError("Ya existe una cuenta con este email.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        auto_active = is_open_registration_window()
        extra = {k: validated_data.pop(k) for k in FESTEJOS_FIELDS if k in validated_data}
        password = validated_data.pop("password")
        pending = User.objects.filter(email=validated_data["email"], registration_status="pending_registration").first()
        if pending:
            for field, value in validated_data.items():
                setattr(pending, field, value)
            pending.set_password(password)
            pending.registration_status = "registered"
            pending.is_active = auto_active
            pending.save()
            user = pending
        else:
            user = User.objects.create_user(**validated_data, password=password, is_active=auto_active)
        sync_festejos_data(user, extra)
        message = f"{user.get_full_name()} ({user.email}) se registró"
        message += " (activo automático por lanzamiento)." if auto_active else " y espera aprobación."
        Notification.objects.create(type=Notification.Type.NEW_REGISTRATION, related_user=user, message=message)
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
    birth_date = serializers.DateField(required=False, allow_null=True, validators=[validate_not_future])
    children = ChildSerializer(many=True, required=False)
    pregnancy = PregnancySerializer(required=False, allow_null=True)
    member_profile = MemberProfileSerializer(read_only=True)
    missing_festejos_data = serializers.SerializerMethodField()

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
            "registration_status",
            "birth_date",
            "children",
            "pregnancy",
            "member_profile",
            "missing_festejos_data",
            "created_at",
        ]
        # is_staff se cambia solo vía la acción set_role (Super Admin); acá queda de solo lectura.
        read_only_fields = ["id", "email", "is_staff", "is_superuser", "registration_status", "created_at"]

    def get_role(self, obj):
        return user_role(obj)

    def get_missing_festejos_data(self, obj):
        return missing_festejos_data(obj)

    @transaction.atomic
    def update(self, instance, validated_data):
        extra = {k: validated_data.pop(k) for k in FESTEJOS_FIELDS if k in validated_data}
        instance = super().update(instance, validated_data)
        sync_festejos_data(instance, extra)
        return instance


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
