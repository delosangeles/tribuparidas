from django.db import migrations


def create_blog_data(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogStage = apps.get_model("blog", "BlogStage")

    categories = [
        ("Salud mental", "salud-mental"),
        ("Crianza", "crianza"),
        ("Alimentación", "alimentacion"),
        ("Sueño", "sueno"),
        ("Estimulación y desarrollo", "estimulacion-y-desarrollo"),
        ("Lactancia", "lactancia"),
        ("Salud y vacunas", "salud-y-vacunas"),
        ("Emprendimiento", "emprendimiento"),
        ("Maternidad y bienestar", "maternidad-y-bienestar"),
        ("Historias de la Tribu", "historias-de-la-tribu"),
    ]

    for order, (name, slug) in enumerate(categories, start=1):
        BlogCategory.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "order": order,
                "is_active": True,
            }
        )

    stages = [
        ("Embarazo", "embarazo"),
        ("0–3 meses", "0-3-meses"),
        ("4–6 meses", "4-6-meses"),
        ("6–12 meses", "6-12-meses"),
        ("1–2 años", "1-2-anos"),
        ("2–4 años", "2-4-anos"),
        ("4+ años", "4-mas-anos"),
        ("Todas las etapas", "todas-las-etapas"),
    ]

    for order, (name, slug) in enumerate(stages, start=1):
        BlogStage.objects.get_or_create(
            slug=slug,
            defaults={
                "name": name,
                "order": order,
                "is_active": True,
            }
        )


def remove_blog_data(apps, schema_editor):
    BlogCategory = apps.get_model("blog", "BlogCategory")
    BlogStage = apps.get_model("blog", "BlogStage")

    BlogCategory.objects.all().delete()
    BlogStage.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            create_blog_data,
            remove_blog_data,
        ),
    ]