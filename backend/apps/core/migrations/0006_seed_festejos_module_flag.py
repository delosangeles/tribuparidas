from django.db import migrations


def create_festejos_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")

    FeatureFlag.objects.get_or_create(
        key="festejos_module",
        defaults={
            "label": "Módulo de Festejos",
            "activate_at": None,
            "is_forced_active": False,
        },
    )


def remove_festejos_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")
    FeatureFlag.objects.filter(key="festejos_module").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_monthlyreport_monthlyreport_reporte_mensual_unico"),
    ]

    operations = [
        migrations.RunPython(
            create_festejos_module_flag,
            remove_festejos_module_flag,
        ),
    ]
