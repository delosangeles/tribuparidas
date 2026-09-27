from django.conf import settings
from django.db import models
from django.utils.text import slugify


class BlogCategory(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="Slug"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Descripción"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden"
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Categoría del blog"
        verbose_name_plural = "Categorías del blog"

    def __str__(self):
        return self.name


class BlogStage(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Nombre"
    )
    slug = models.SlugField(
        max_length=120,
        unique=True,
        verbose_name="Slug"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Activa"
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Orden"
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Etapa del blog"
        verbose_name_plural = "Etapas del blog"

    def __str__(self):
        return self.name


class BlogPost(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        IN_REVIEW = "IN_REVIEW", "En revisión"
        PUBLISHED = "PUBLISHED", "Publicado"

    class ContentType(models.TextChoices):
        ARTICLE = "ARTICLE", "Artículo"
        GUIDE = "GUIDE", "Guía"
        CHECKLIST = "CHECKLIST", "Checklist"
        RESOURCE = "RESOURCE", "Recurso"
        RECOMMENDATION = "RECOMMENDATION", "Recomendación"
        TRIBU_STORY = "TRIBU_STORY", "Historia de la Tribu"

    title = models.CharField(
        max_length=250,
        verbose_name="Título"
    )

    slug = models.SlugField(
        max_length=280,
        unique=True,
        verbose_name="Slug"
    )

    summary = models.TextField(
        verbose_name="Resumen"
    )

    content = models.TextField(
        verbose_name="Contenido"
    )

    main_image = models.ImageField(
        upload_to="blog/",
        blank=True,
        null=True,
        verbose_name="Imagen principal"
    )

    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.PROTECT,
        related_name="posts",
        verbose_name="Categoría"
    )

    stages = models.ManyToManyField(
        BlogStage,
        related_name="posts",
        blank=True,
        verbose_name="Etapas"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="blog_posts",
        verbose_name="Autor"
    )

    content_type = models.CharField(
        max_length=30,
        choices=ContentType.choices,
        default=ContentType.ARTICLE,
        verbose_name="Tipo de contenido"
    )

    publication_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Fecha de publicación"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name="Estado"
    )

    featured = models.BooleanField(
        default=False,
        verbose_name="Destacado"
    )

    reading_time = models.PositiveIntegerField(
        default=1,
        verbose_name="Tiempo de lectura (minutos)"
    )

    sources = models.TextField(
        blank=True,
        verbose_name="Fuentes / referencias"
    )

    seo_title = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="SEO title"
    )

    seo_description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="SEO description"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        ordering = ["-publication_date", "-created_at"]
        verbose_name = "Publicación del blog"
        verbose_name_plural = "Publicaciones del blog"

    def __str__(self):
        return self.title


class BlogComment(models.Model):
    post = models.ForeignKey(
        BlogPost,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Publicación"
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comments",
        verbose_name="Autor"
    )

    content = models.TextField(
        verbose_name="Comentario"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Comentario del blog"
        verbose_name_plural = "Comentarios del blog"

    def __str__(self):
        return f"{self.author} -> {self.post}: {self.content[:30]}"