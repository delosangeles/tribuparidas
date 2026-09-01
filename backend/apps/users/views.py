import secrets

from rest_framework import generics, mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import log_activity
from apps.core.permissions import IsSuperAdmin

from .models import Notification, User
from .serializers import (
    AdminUserCreateSerializer,
    AdminUserSerializer,
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    MeUpdateSerializer,
    NotificationSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
    is_open_registration_window,
    user_role,
)


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — normalmente queda inactiva (sin tokens: no
    hay auto-login) hasta que un admin la aprueba manualmente. Durante la
    ventana de lanzamiento (ver is_open_registration_window) queda activa
    de una vez y puede iniciar sesión directo."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if is_open_registration_window():
            detail = "¡Registro recibido! Tu cuenta ya está activa, puedes iniciar sesión."
        else:
            detail = "¡Registro recibido! Tu cuenta está en revisión, te avisaremos cuando quede aprobada."
        return Response(
            {"detail": detail, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/login/"""

    serializer_class = CustomTokenObtainPairSerializer


class LogoutView(APIView):
    """POST /api/auth/logout/ — invalida el refresh token (blacklist)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "El campo 'refresh' es requerido."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({"detail": "Token inválido o ya expirado."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class PasswordResetRequestView(APIView):
    """POST /api/auth/password-reset-request/ — no hay email: solo le avisa
    al equipo admin (notificación interna) para que resetee la contraseña a mano."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Le avisamos al equipo. Te contactarán por WhatsApp para ayudarte a recuperar el acceso."},
            status=status.HTTP_200_OK,
        )


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PUT/PATCH /api/me/"""

    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return MeUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """POST /api/me/change-password/ — autoservicio: la usuaria cambia su
    propia contraseña conociendo la actual (distinto del reset que hace un admin)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Contraseña actualizada."})


class AdminUserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """/api/admin/users/ — el admin puede activar/desactivar cuentas y editar
    nombre/apellido/WhatsApp; el email y el rol no se tocan desde acá."""

    queryset = User.objects.all().order_by("-created_at")
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_active", "is_staff"]
    search_fields = ["email", "first_name", "last_name"]
    ordering_fields = ["created_at", "email"]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_permissions(self):
        if self.action == "create":
            return [IsSuperAdmin()]
        return super().get_permissions()

    def create(self, request, *args, **kwargs):
        """POST /api/admin/users/ — solo Super Admin: crea la cuenta directo
        (ya activa, sin pasar por el registro público) y puede asignarle de
        una vez el rol Administrador."""
        serializer = AdminUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_activity(
            request.user,
            "user_created_by_admin",
            f"{request.user.email} creó la cuenta de {user.email} ({user_role(user)}).",
            target=user,
        )
        return Response(
            {**AdminUserSerializer(user).data, "new_password": user.generated_password},
            status=status.HTTP_201_CREATED,
        )

    def perform_update(self, serializer):
        was_active = serializer.instance.is_active
        before = (serializer.instance.first_name, serializer.instance.last_name, serializer.instance.whatsapp)
        user = serializer.save()

        if user.is_active != was_active:
            action_name = "user_activated" if user.is_active else "user_deactivated"
            verb = "activó" if user.is_active else "desactivó"
            log_activity(self.request.user, action_name, f"{self.request.user.email} {verb} a {user.email}.", target=user)

        if (user.first_name, user.last_name, user.whatsapp) != before:
            log_activity(
                self.request.user, "user_info_updated", f"{self.request.user.email} editó los datos de {user.email}.", target=user
            )

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        """Genera una contraseña nueva y la devuelve para que el admin se la
        pase a la usuaria por WhatsApp (no hay envío de correo)."""
        user = self.get_object()
        new_password = secrets.token_urlsafe(9)
        user.set_password(new_password)
        user.save(update_fields=["password"])
        log_activity(
            request.user, "user_password_reset", f"{request.user.email} reseteó la contraseña de {user.email}.", target=user
        )
        return Response({"new_password": new_password})

    @action(detail=True, methods=["post"], permission_classes=[IsSuperAdmin])
    def set_role(self, request, pk=None):
        """Solo Super Admin: asciende a Administrador o degrada a Usuario.
        No otorga/quita superusuario — eso se maneja fuera de la API."""
        user = self.get_object()
        is_staff = request.data.get("is_staff")
        if not isinstance(is_staff, bool):
            raise serializers.ValidationError({"is_staff": "Debe ser true o false."})
        if user.is_superuser:
            raise serializers.ValidationError({"detail": "No se puede cambiar el rol de un Super Admin desde aquí."})

        user.is_staff = is_staff
        user.save(update_fields=["is_staff"])
        action_name = "user_promoted_admin" if is_staff else "user_demoted_admin"
        verb = "ascendió a Administrador" if is_staff else "quitó el rol de Administrador a"
        log_activity(request.user, action_name, f"{request.user.email} {verb} {user.email}.", target=user)
        return Response(AdminUserSerializer(user).data)


class NotificationViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """/api/admin/notifications/ — avisos internos para el equipo admin."""

    queryset = Notification.objects.all().select_related("related_user")
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_read", "type"]
    http_method_names = ["get", "patch", "post", "head", "options"]

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response(status=status.HTTP_204_NO_CONTENT)
