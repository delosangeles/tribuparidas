from django.db import migrations

# Categorías del menú principal del blog. Las que ya existen (Emprendimiento,
# Sueño, Alimentación, Salud y vacunas) no se tocan ni se renombran: el menú
# las enlaza por su slug. Solo se crean las que faltan.
NEW_CATEGORIES = [
    ("Encuentros", "encuentros"),
    ("Fit", "fit"),
    ("Lecturas", "lecturas"),
    ("12-24+", "12-24"),
    ("Iniciativas Sociales", "iniciativas-sociales"),
    ("Las Encendidas", "las-encendidas"),
    ("Embarazo", "embarazo"),
]


def create_categories(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    last_order = max(BlogCategory.objects.values_list("order", flat=True), default=0)
    for offset, (name, slug) in enumerate(NEW_CATEGORIES, start=1):
        BlogCategory.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "order": last_order + offset, "is_active": True},
        )


def remove_categories(apps, schema_editor):
    # Solo borra las que no tienen publicaciones, para no perder contenido.
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogCategory.objects.filter(slug__in=[s for _, s in NEW_CATEGORIES], posts__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0007_blogpost_visibility"),
    ]

    operations = [
        migrations.RunPython(create_categories, remove_categories),
    ]
