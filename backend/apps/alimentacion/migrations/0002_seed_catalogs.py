from django.db import migrations

# Solo los catálogos que definió el equipo (rangos de edad y tipos de comida).
# Los alérgenos NO se siembran: los carga el equipo tras la revisión del profesional.
AGES = [("6-8 meses", "6-8-meses"), ("9-11 meses", "9-11-meses"), ("12+ meses", "12-meses")]
MEAL_TYPES = [
    ("Puré", "pure"),
    ("Trozos / BLW", "trozos-blw"),
    ("Desayuno", "desayuno"),
    ("Almuerzo", "almuerzo"),
    ("Snack", "snack"),
]


def seed(apps, schema_editor):
    AgeRange = apps.get_model("alimentacion", "AgeRange")
    MealType = apps.get_model("alimentacion", "MealType")
    for order, (name, slug) in enumerate(AGES):
        AgeRange.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})
    for order, (name, slug) in enumerate(MEAL_TYPES):
        MealType.objects.get_or_create(slug=slug, defaults={"name": name, "order": order})


class Migration(migrations.Migration):

    dependencies = [("alimentacion", "0001_initial")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
