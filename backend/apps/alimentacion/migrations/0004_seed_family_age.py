from django.db import migrations


def seed(apps, schema_editor):
    AgeRange = apps.get_model("alimentacion", "AgeRange")
    AgeRange.objects.get_or_create(slug="familia-adultos", defaults={"name": "Familia / adultos", "order": 3})


class Migration(migrations.Migration):

    dependencies = [("alimentacion", "0003_cookbook")]

    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
