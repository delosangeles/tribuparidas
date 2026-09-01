from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class TimeStampedModel(models.Model):
    """Abstracto: agrega created_at/updated_at a cualquier modelo que lo herede."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActivityLog(models.Model):
    """Historial de acciones de moderación admin (aprobar negocios, activar
    usuarios, categorías, cambios de rol, etc.) — no registra lo que hacen
    las emprendedoras con sus propios datos."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="activity_logs"
    )
    action = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.description


def log_activity(actor, action, description, target=None):
    """Registra una acción admin en el historial. `target` es la instancia
    afectada (Business, Category, User...), opcional."""
    ActivityLog.objects.create(
        actor=actor,
        action=action,
        description=description,
        content_type=ContentType.objects.get_for_model(target) if target is not None else None,
        object_id=target.pk if target is not None else None,
    )
