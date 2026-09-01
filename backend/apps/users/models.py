from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model: el email es el identificador de login (sin username)."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    # Al registrarse queda inactiva hasta que un admin confirma que pertenece
    # al grupo de WhatsApp de la tribu (ver RegisterSerializer).
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        return self.first_name or self.email

    @property
    def is_entrepreneur(self):
        return self.businesses.exists()


class Notification(models.Model):
    """Aviso interno para el equipo admin (sin correo/WhatsApp externo):
    nueva persona registrada esperando aprobación, o alguien que olvidó su
    contraseña y necesita que se la reseteen manualmente."""

    class Type(models.TextChoices):
        NEW_REGISTRATION = "new_registration", "Nuevo registro"
        PASSWORD_RESET_REQUEST = "password_reset_request", "Olvidó su contraseña"

    type = models.CharField(max_length=30, choices=Type.choices)
    message = models.CharField(max_length=255)
    related_user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications_about_me"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.message
