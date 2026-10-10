from django.db import migrations


def create_desahogos(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogCategory.objects.get_or_create(
        slug="desahogos",
        defaults={
            "name": "Desahogos",
            "description": (
                "Un espacio para soltar lo que llevas dentro. Aquí cualquier mamá de la tribu "
                "puede publicar sin aprobación previa."
            ),
            "order": 11,
            "is_active": True,
        },
    )


def remove_desahogos(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogCategory.objects.filter(slug="desahogos", posts__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0005_comments_and_confirmation"),
    ]

    operations = [
        migrations.RunPython(create_desahogos, remove_desahogos),
    ]
