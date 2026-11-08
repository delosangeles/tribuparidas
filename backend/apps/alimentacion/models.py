from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.models import TimeStampedModel
from apps.core.validators import validate_image_file

from .text import normalize_text


class Status(models.TextChoices):
    """Estado de publicación. Es un CharField con `choices`, así que añadir
    "en revisión" más adelante solo es sumar un valor aquí."""

    DRAFT = "draft", "Borrador"
    PUBLISHED = "published", "Publicado"


def unique_slug(model, base, instance=None, max_length=140):
    base = (slugify(base) or "item")[: max_length - 8]
    slug, n = base, 2
    qs = model.objects.all()
    if instance is not None and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


class SluggedModel(TimeStampedModel):
    """Genera `slug` a partir de `slug_source` si viene vacío."""

    slug = models.SlugField(max_length=140, unique=True, blank=True)
    slug_source = "name"

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(type(self), getattr(self, self.slug_source), self)
        super().save(*args, **kwargs)


class CatalogItem(SluggedModel):
    name = models.CharField(max_length=100, verbose_name="Nombre")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden")
    is_active = models.BooleanField(default=True, verbose_name="Activo")

    class Meta:
        abstract = True
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class AgeRange(CatalogItem):
    class Meta(CatalogItem.Meta):
        verbose_name = "Rango de edad"
        verbose_name_plural = "Rangos de edad"


class Allergen(CatalogItem):
    class Meta(CatalogItem.Meta):
        verbose_name = "Alérgeno"
        verbose_name_plural = "Alérgenos"


class MealType(CatalogItem):
    """Tipo de comida: puré, trozos/BLW, desayuno, almuerzo, snack…"""

    class Meta(CatalogItem.Meta):
        verbose_name = "Tipo de comida"
        verbose_name_plural = "Tipos de comida"


class GuideArticle(SluggedModel):
    slug_source = "title"

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    content = models.TextField(blank=True, help_text="HTML sanitizado del editor.")
    image = models.ImageField(upload_to="alimentacion/guides/", blank=True, null=True, validators=[validate_image_file])
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Guía de inicio"
        verbose_name_plural = "Guías de inicio"

    def __str__(self):
        return self.title


class Recipe(SluggedModel):
    slug_source = "title"

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    image = models.ImageField(upload_to="alimentacion/recipes/", blank=True, null=True, validators=[validate_image_file])
    age_range = models.ForeignKey(AgeRange, on_delete=models.PROTECT, related_name="recipes")
    meal_type = models.ForeignKey(MealType, on_delete=models.PROTECT, related_name="recipes")
    prep_time_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    allergens = models.ManyToManyField(Allergen, blank=True, related_name="recipes")
    storage_tip = models.TextField(blank=True, verbose_name="Consejo de conservación")
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    # Título + ingredientes sin tildes, para el buscador.
    search_text = models.TextField(blank=True, editable=False)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Receta"
        verbose_name_plural = "Recetas"

    def __str__(self):
        return self.title

    def refresh_search_text(self):
        names = " ".join(self.ingredients.values_list("name", flat=True)) if self.pk else ""
        self.search_text = normalize_text(f"{self.title} {self.summary} {names}")
        Recipe.objects.filter(pk=self.pk).update(search_text=self.search_text)

    def save(self, *args, **kwargs):
        self.search_text = normalize_text(f"{self.title} {self.summary}")
        super().save(*args, **kwargs)
        if kwargs.get("update_fields") is None:
            self.refresh_search_text()


class RecipeIngredient(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ingredients")
    name = models.CharField(max_length=200)
    quantity = models.CharField(max_length=100, blank=True, help_text="Texto libre; lo escribe el equipo.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class RecipeStep(TimeStampedModel):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    text = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class FoodItem(SluggedModel):
    name = models.CharField(max_length=150)
    age_range = models.ForeignKey(AgeRange, on_delete=models.PROTECT, null=True, blank=True, related_name="foods")
    how_to_offer = models.TextField(blank=True, verbose_name="Cómo ofrecerlo (forma y textura)")
    is_common_allergen = models.BooleanField(default=False)
    allergen = models.ForeignKey(Allergen, on_delete=models.SET_NULL, null=True, blank=True, related_name="foods")
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Alimento"
        verbose_name_plural = "Alimentos"

    def __str__(self):
        return self.name


class SafetyContent(TimeStampedModel):
    """Sección fija de seguridad (un solo registro): atragantamiento vs.
    arcadas, alimentos a evitar y reacción alérgica. La redacta y firma un
    profesional; mientras no esté publicada no se muestra."""

    content = models.TextField(blank=True)
    professional_name = models.CharField(max_length=150, blank=True)
    professional_title = models.CharField(max_length=150, blank=True)
    reviewed_on = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    class Meta:
        verbose_name = "Contenido de seguridad"
        verbose_name_plural = "Contenido de seguridad"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class FavoriteRecipe(TimeStampedModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_recipes")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="favorites")

    class Meta:
        ordering = ["-created_at"]
        constraints = [models.UniqueConstraint(fields=["user", "recipe"], name="receta_favorita_unica")]
