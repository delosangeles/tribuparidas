from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.core.validators import validate_image_file


# Única categoría donde cualquier persona registrada publica sin aprobación
# previa del equipo admin. En las demás, el blog queda "en revisión".
OPEN_CATEGORY_SLUG = "desahogos"


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

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Público"
        PRIVATE = "private", "Privado"

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

    # Público: lo ve cualquiera, incluso sin iniciar sesión. Privado: solo
    # quien tiene sesión. Los blogs que ya existían quedan públicos; al crear
    # uno por la API es obligatorio elegir (ver BlogPostWriteSerializer).
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PUBLIC,
        verbose_name="Visibilidad"
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


def comment_image_path(instance, filename):
    # Nombre aleatorio: no se puede adivinar la URL de la foto de otra persona.
    import os
    import uuid

    return f"blog/comments/{uuid.uuid4().hex}{os.path.splitext(filename)[1].lower()}"


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

    # Puede ir vacío cuando el comentario es solo una foto.
    content = models.TextField(
        blank=True,
        verbose_name="Comentario"
    )

    # Respuestas: un solo nivel. Responder a una respuesta se guarda como
    # respuesta del comentario principal (ver BlogCommentCreateSerializer).
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="replies",
        verbose_name="Responde a"
    )

    image = models.ImageField(
        upload_to=comment_image_path,
        null=True,
        blank=True,
        validators=[validate_image_file],
        verbose_name="Foto"
    )

    edited_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Editado"
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


class BlogCommentLike(models.Model):
    """Reacción "me gusta" a un comentario (una por persona)."""

    comment = models.ForeignKey(
        BlogComment,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blog_comment_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["comment", "user"], name="blog_comment_like_unico"),
        ]

    def __str__(self):
        return f"{self.user} ♥ {self.comment_id}"