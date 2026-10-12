import os
import uuid

from django.conf import settings
from django.db import models

from apps.core.validators import validate_image_file


def festejo_photo_path(instance, filename):
    # Nombre aleatorio: las fotos se sirven desde /media/ y no deben poder adivinarse.
    return f"festejos/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"


class Festejo(models.Model):
    """Una celebración (mesversario, cumpleaños de hijo o de madre). Se genera
    automáticamente desde el perfil y un admin la aprueba antes de que la
    vea el resto de la tribu; también se pueden crear a mano."""

    class Kind(models.TextChoices):
        MONTHIVERSARY = "monthiversary", "Mesversario"
        CHILD_BIRTHDAY = "child_birthday", "Cumpleaños de hijo/a"
        MOTHER_BIRTHDAY = "mother_birthday", "Cumpleaños de mamá"
        MANUAL = "manual", "Festejo manual"

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobado"

    kind = models.CharField(max_length=20, choices=Kind.choices)
    event_date = models.DateField()
    # Madre a la que se asigna el festejo (también el del hijo/a).
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="festejos")
    child = models.ForeignKey("users.Child", on_delete=models.CASCADE, null=True, blank=True, related_name="festejos")
    # Meses (mesversario) o años (cumpleaños) que se cumplen.
    number = models.PositiveSmallIntegerField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True)
    note = models.TextField(blank=True)
    # Imagen propia del festejo (se sube al crear uno manual). Si no tiene, la tarjeta
    # usa la foto del hijo/a o de la mamá.
    photo = models.ImageField(upload_to=festejo_photo_path, blank=True, null=True, validators=[validate_image_file])
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    is_manual = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["event_date", "id"]
        constraints = [
            # Evita duplicados si el cálculo corre más de una vez.
            models.UniqueConstraint(
                fields=["kind", "user", "child", "event_date"],
                name="festejo_unico_por_persona_y_fecha",
                nulls_distinct=False,
            ),
        ]

    def __str__(self):
        return f"{self.get_kind_display()} {self.event_date} ({self.user.email})"
