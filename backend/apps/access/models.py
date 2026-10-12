from django.conf import settings
from django.db import models


class ModuleAccess(models.Model):
    """Acceso de una "madrina" a un módulo del panel de administración, con las
    acciones que puede hacer. Las administradoras actuales (is_staff) no
    necesitan filas: conservan acceso total. En el módulo blog, `categories`
    limita a qué categorías aplica (vacío = todas)."""

    class Module(models.TextChoices):
        USUARIOS = "usuarios", "Usuarios"
        BLOG = "blog", "Blog"
        FESTEJOS = "festejos", "Festejos"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="module_access")
    module = models.CharField(max_length=20, choices=Module.choices)
    can_add = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    categories = models.ManyToManyField("blog.BlogCategory", blank=True, related_name="madrinas")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["module"]
        constraints = [models.UniqueConstraint(fields=["user", "module"], name="acceso_unico_por_usuaria_y_modulo")]

    def __str__(self):
        return f"{self.user} · {self.module}"
