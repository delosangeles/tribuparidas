from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.categories.models import Category
from apps.core.models import TimeStampedModel
from apps.core.validators import validate_image_file


class Business(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        APPROVED = "approved", "Aprobado"
        REJECTED = "rejected", "Rechazado"

    class BenefitType(models.TextChoices):
        DESCUENTO = "descuento", "Descuento"
        ENVIO_GRATIS = "envio_gratis", "Envío gratis"
        PROMOCION = "promocion", "Promoción"
        PRECIO_ESPECIAL = "precio_especial", "Precio especial"
        BENEFICIO_EXCLUSIVO = "beneficio_exclusivo", "Beneficio exclusivo"
        OTRO = "otro", "Otro"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="businesses"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    logo = models.ImageField(upload_to="businesses/logos/", blank=True, null=True, validators=[validate_image_file])
    cover_image = models.ImageField(
        upload_to="businesses/covers/", blank=True, null=True, validators=[validate_image_file]
    )
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="businesses")
    city = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    address = models.CharField(max_length=255, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    instagram = models.CharField(max_length=100, blank=True)
    facebook = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    opening_hours = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)

    # Campos del directorio de beneficios de la tribu
    home_delivery = models.BooleanField("¿Ofrece domicilio?", default=False)
    tribe_benefit = models.BooleanField("¿Tiene beneficio tribu?", default=False)
    benefit_type = models.CharField(
        "Tipo de beneficio", max_length=20, choices=BenefitType.choices, blank=True
    )
    benefit_detail = models.TextField("Detalle del beneficio", blank=True)
    is_mama_tribu = models.BooleanField("¿Emprendimiento de mamá tribu?", default=False)
    responsible_name = models.CharField("Responsable", max_length=150, blank=True)
    tribe_recommended = models.BooleanField("¿Recomendado por la tribu?", default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "businesses"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)


class BusinessImage(TimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="businesses/gallery/", validators=[validate_image_file])
    caption = models.CharField(max_length=150, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return f"{self.business.name} - {self.caption or self.pk}"
