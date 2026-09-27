from django.db import migrations


def create_blog_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")

    FeatureFlag.objects.get_or_create(
        key="blog_module",
        defaults={
            "label": "Módulo de Blog",
            "activate_at": None,
            "is_forced_active": False,
        },
    )


def remove_blog_module_flag(apps, schema_editor):
    FeatureFlag = apps.get_model("core", "FeatureFlag")
    FeatureFlag.objects.filter(key="blog_module").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_featureflag"),
    ]

    operations = [
        migrations.RunPython(
            create_blog_module_flag,
            remove_blog_module_flag,
        ),
    ]
