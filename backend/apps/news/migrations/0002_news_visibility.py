from django.db import migrations, models


class Migration(migrations.Migration):
    """Campo obligatorio `visibility`. Las noticias que ya existían quedan
    como privadas (el default solo se usa para rellenarlas)."""

    dependencies = [
        ("news", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="news",
            name="visibility",
            field=models.CharField(
                choices=[("public", "Pública"), ("private", "Privada")],
                default="private",
                max_length=10,
                verbose_name="Visibilidad",
            ),
            preserve_default=False,
        ),
    ]
