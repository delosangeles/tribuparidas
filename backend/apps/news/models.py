from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel
from apps.core.validators import validate_image_file


class News(TimeStampedModel):
    title = models.CharField(
        "Título",
        max_length=200,
    )

    description = models.TextField(
        "Descripción",
        blank=True,
    )

    image_desktop = models.ImageField(
        "Imagen para PC",
        upload_to="news/desktop/",
        validators=[validate_image_file],
    )

    image_mobile = models.ImageField(
        "Imagen para móvil",
        upload_to="news/mobile/",
        validators=[validate_image_file],
    )

    link = models.URLField(
        "Enlace",
        blank=True,
    )

    published_at = models.DateTimeField(
        "Fecha de publicación",
    )

    expires_at = models.DateTimeField(
        "Fecha de vencimiento",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_news",
        verbose_name="Creado por",
    )
    order = models.PositiveIntegerField("Orden", default=0)
    is_active = models.BooleanField(
        "Activo",
        default=True,
    )

    class Meta:
        ordering = ["-published_at"]
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"

    def __str__(self):
        return self.title