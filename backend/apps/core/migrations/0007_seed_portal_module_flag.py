from django.db import migrations


def create_portal_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")

    FeatureFlag.objects.get_or_create(
        key="portal_module",
        defaults={
            "label": "Portal de emprendimientos y Mi tarjeta",
            "activate_at": None,
            "is_forced_active": False,
        },
    )


def remove_portal_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")
    FeatureFlag.objects.filter(key="portal_module").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_seed_festejos_module_flag"),
    ]

    operations = [
        migrations.RunPython(
            create_portal_module_flag,
            remove_portal_module_flag,
        ),
    ]
