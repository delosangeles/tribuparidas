from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.core.validators import validate_image_file


class Category(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True, validators=[validate_image_file])
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subcategories",
        help_text="Déjalo vacío si esta es una categoría principal.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return f"{self.parent.name} / {self.name}" if self.parent_id else self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError("Una categoría no puede ser su propia categoría padre.")
        if self.parent_id and self.parent.parent_id:
            raise ValidationError("Solo se permiten dos niveles: categoría y subcategoría.")
