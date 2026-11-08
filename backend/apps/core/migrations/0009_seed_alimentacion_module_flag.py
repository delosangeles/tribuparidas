from django.db import migrations


def create_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")

    FeatureFlag.objects.get_or_create(
        key="alimentacion_module",
        defaults={
            "label": "Módulo de Alimentación Complementaria",
            "activate_at": None,
            "is_forced_active": False,
        },
    )


def remove_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")
    FeatureFlag.objects.filter(key="alimentacion_module").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_sitesetting"),
    ]

    operations = [
        migrations.RunPython(create_flag, remove_flag),
    ]
