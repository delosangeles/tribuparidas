from django.db import models


class TimeStampedModel(models.Model):
    """Abstracto: agrega created_at/updated_at a cualquier modelo que lo herede."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
