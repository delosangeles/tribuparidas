from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


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


class PageView(models.Model):
    """Una vista de página del sitio, para analítica de uso (solo Super Admin
    la consulta). `session_id` lo genera el navegador (sessionStorage) para
    poder agrupar las vistas de una misma visita sin depender de cookies de
    sesión de Django (la auth es JWT, sin sesión de servidor)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="page_views"
    )
    session_id = models.CharField(max_length=40)
    path = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["session_id", "created_at"])]


class FeatureFlag(models.Model):
    """Interruptor con activación programada: el código de una funcionalidad
    ya puede estar desplegado en producción, oculto hasta una fecha/hora que
    el Super Admin define desde `/admin/lanzamiento` — el mismo espíritu del
    portón de lanzamiento del sitio (`frontend/app.vue`), pero reutilizable
    para cualquier módulo futuro sin tocar código ni volver a desplegar."""

    key = models.SlugField(
        unique=True,
        verbose_name="Clave"
    )

    label = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )

    activate_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha y hora de activación"
    )

    is_forced_active = models.BooleanField(
        default=False,
        verbose_name="Forzar activación inmediata"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Última actualización"
    )

    class Meta:
        ordering = ["key"]
        verbose_name = "Interruptor de funcionalidad"
        verbose_name_plural = "Interruptores de funcionalidad"

    def __str__(self):
        return self.label

    @property
    def is_active(self):
        if self.is_forced_active:
            return True
        if self.activate_at is None:
            return False
        return timezone.now() >= self.activate_at


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


class MonthlyReport(models.Model):
    """Reporte mensual de la plataforma. Se genera UNA sola vez, el primer día
    de cada mes, para el mes anterior, y queda guardado tal cual: no se
    recalcula ni se sobrescribe (los números quedan "congelados")."""

    year = models.PositiveSmallIntegerField()
    month = models.PositiveSmallIntegerField()
    data = models.JSONField()
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-year", "-month"]
        constraints = [models.UniqueConstraint(fields=["year", "month"], name="reporte_mensual_unico")]

    def __str__(self):
        return f"Reporte {self.year}-{self.month:02d}"
