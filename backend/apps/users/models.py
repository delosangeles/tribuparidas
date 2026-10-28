import os
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.core.validators import validate_image_file, validate_phone_with_country_code

from .managers import UserManager


def _unguessable_name(folder, filename):
    # Nombre aleatorio: las fotos se sirven desde /media/, así que la URL no
    # debe poder adivinarse (las de los hijos son solo para la tribu).
    return f"{folder}/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"


def user_photo_path(instance, filename):
    return _unguessable_name("users/photos", filename)


def child_photo_path(instance, filename):
    return _unguessable_name("users/children", filename)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model: el email es el identificador de login (sin username)."""

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    # Teléfono de contacto: es el mismo WhatsApp con el que el equipo admin
    # confirma que la persona está en el grupo de la tribu.
    whatsapp = models.CharField(max_length=30, blank=True, validators=[validate_phone_with_country_code])
    # Cédula: única (sin duplicados entre cuentas) y solo visible para la propia
    # usuaria y el equipo admin. Nula (no vacía) cuando falta, para que el
    # índice único no choque entre cuentas que aún no la tienen.
    document_id = models.CharField(max_length=30, unique=True, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True)
    department = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to=user_photo_path, blank=True, null=True, validators=[validate_image_file])
    # Al registrarse queda inactiva hasta que un admin confirma que pertenece
    # al grupo de WhatsApp de la tribu (ver RegisterSerializer).
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    # Fecha de cumpleaños de la madre (festejos). Opcional a nivel de base de
    # datos para no romper usuarias existentes; la API la exige al registrarse.
    birth_date = models.DateField(null=True, blank=True)
    # "pending_registration": cuenta precargada desde el Excel de inscripción
    # cuya dueña aún no se ha registrado (sin contraseña, inactiva).
    registration_status = models.CharField(
        max_length=25,
        choices=[("registered", "Registrada"), ("pending_registration", "Pendiente de registrarse")],
        default="registered",
    )
    # Datos precargados desde el Excel de inscripción: al entrar, la persona ve
    # un aviso para revisarlos, corregirlos y confirmarlos. Se apaga al confirmar.
    needs_data_confirmation = models.BooleanField(default=False)
    # "member": usuaria de la página (ve todo el sitio). "portal": cuenta solo
    # para gestionar un emprendimiento en /portal; un admin la puede convertir.
    account_type = models.CharField(
        max_length=10,
        choices=[("member", "Usuaria de la página"), ("portal", "Solo portal")],
        default="member",
    )
    data_confirmed_at = models.DateTimeField(null=True, blank=True)
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
        MEMBER_CONVERSION_REQUEST = "member_conversion_request", "Pide pasar a usuaria de la página"

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


class Child(models.Model):
    """Hijo/a de una usuaria (datos de menores: solo los ve la propia usuaria
    y el equipo admin). Nombre y fecha son obligatorios en la API; en base de
    datos quedan opcionales por si la importación trae datos incompletos."""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=150, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to=child_photo_path, blank=True, null=True, validators=[validate_image_file])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["birth_date", "id"]
        verbose_name_plural = "children"

    def __str__(self):
        return f"{self.name} ({self.user.email})"


class Pregnancy(models.Model):
    """Embarazo en curso: fecha probable de parto. No genera mesversarios."""

    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="pregnancy")
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Embarazo de {self.user.email} ({self.due_date})"


class MemberProfile(models.Model):
    """Respuestas del formulario de inscripción "TRIBU PARIDAS Conociéndonos".
    Todo opcional: lo llena la importación del Excel o la propia usuaria."""

    user = models.OneToOneField("users.User", on_delete=models.CASCADE, related_name="member_profile")
    preferred_name = models.CharField(max_length=150, blank=True)
    location = models.CharField(max_length=255, blank=True)
    occupation = models.CharField(max_length=255, blank=True)
    situation = models.CharField(max_length=255, blank=True)  # ¿Estás?
    children_text = models.TextField(blank=True)  # nombre y edad de los hijos (texto libre original)
    companions = models.CharField(max_length=255, blank=True)
    how_met = models.CharField(max_length=255, blank=True)
    invited_by = models.CharField(max_length=255, blank=True)
    interests = models.TextField(blank=True)
    has_business = models.CharField(max_length=100, blank=True)
    business_description = models.TextField(blank=True)
    business_social = models.CharField(max_length=500, blank=True)
    offers_benefits = models.CharField(max_length=255, blank=True)
    looking_for = models.TextField(blank=True)
    desired_professional = models.TextField(blank=True)
    meaning_phrase = models.TextField(blank=True)
    spaces = models.TextField(blank=True)
    main_need = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    form_submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.email}"
