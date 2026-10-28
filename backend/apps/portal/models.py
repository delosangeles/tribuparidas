from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.businesses.models import Business
from apps.core.models import TimeStampedModel
from apps.reviews.models import Review

CONSENT_VERSION = "2026-10-v1"


class BusinessOwner(models.Model):
    """Persona con acceso al portal de un emprendimiento aprobado. Pueden ser
    varias por emprendimiento: la dueña (gestiona todo) y vendedoras (solo
    escanean y ven estadísticas)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Dueña"
        SELLER = "seller", "Vendedora"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="portal_access")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="portal_members")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.OWNER)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["business_id", "role", "id"]
        constraints = [models.UniqueConstraint(fields=["user", "business"], name="portal_acceso_unico")]

    def __str__(self):
        return f"{self.user} · {self.business} ({self.role})"


class BusinessBenefit(TimeStampedModel):
    """Beneficio Tribu de un emprendimiento (descuento porcentual). Todo cambio
    vuelve el estado a "pendiente": solo un beneficio aprobado se publica y
    se puede canjear."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente de aprobación"
        APPROVED = "approved", "Aprobado"
        REJECTED = "rejected", "Rechazado"

    business = models.OneToOneField(Business, on_delete=models.CASCADE, related_name="benefit")
    percentage = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    conditions = models.TextField(blank=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.business}: {self.percentage}%"

    def is_valid_on(self, day):
        if self.status != self.Status.APPROVED:
            return False
        if self.valid_from and day < self.valid_from:
            return False
        if self.valid_until and day > self.valid_until:
            return False
        return True


class BusinessFAQ(TimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="faqs")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class ReviewReply(TimeStampedModel):
    """Respuesta pública de la dueña a una opinión (una por opinión)."""

    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="reply")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    text = models.TextField(max_length=1000)


class CardVisit(models.Model):
    """Alguien abrió la tarjeta pública del emprendimiento."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="card_visits")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="card_visits"
    )
    session_id = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["business", "created_at"])]


class DiscountRedemption(models.Model):
    """Descuento aplicado. `local_date` (día de Bogotá) con la restricción
    única garantiza a nivel de base de datos "una vez al día" aun con
    escaneos simultáneos."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="redemptions")
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="redemptions")
    percentage = models.PositiveSmallIntegerField()
    redeemed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    local_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "business", "local_date"], name="canje_unico_por_dia")
        ]
        indexes = [models.Index(fields=["business", "created_at"])]


class DataSharingConsent(models.Model):
    """Consentimiento (Ley 1581 de 2012) para compartir nombre, teléfono y
    correo con los emprendimientos al usar la tarjeta."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="data_sharing_consent")
    version = models.CharField(max_length=20, default=CONSENT_VERSION)
    accepted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        return self.revoked_at is None


class Membership(models.Model):
    """Membresía de la usuaria. Sin fila = activa (todas las cuentas aprobadas
    lo son por defecto); la fila solo existe cuando un admin la cambia."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="membership")
    is_active = models.BooleanField(default=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)


class CardCode(models.Model):
    """Código de respaldo de 6 dígitos de la tarjeta (vence con el QR)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="card_code")
    code = models.CharField(max_length=6, db_index=True)
    expires_at = models.DateTimeField()


class MemberNotice(models.Model):
    """Aviso a la usuaria (ej. "se aplicó tu descuento en X")."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notices")
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class BusinessChangeLog(models.Model):
    """Trazabilidad de lo que cambian las personas del portal sobre su emprendimiento."""

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="change_logs")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    entity = models.CharField(max_length=20)  # business | benefit | faq | image | review_reply
    action = models.CharField(max_length=20)  # update | create | delete | reorder
    changes = models.JSONField(default=dict)  # {campo: {"from": x, "to": y}}
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
