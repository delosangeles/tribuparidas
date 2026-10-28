from django.db import migrations


def seed_owners(apps, schema_editor):
    """Las dueñas actuales (Business.owner) de emprendimientos aprobados reciben
    acceso al portal como "dueña", sin tocar nada más."""
    Business = apps.get_model("businesses", "Business")
    BusinessOwner = apps.get_model("portal", "BusinessOwner")
    for business in Business.objects.filter(status="approved").select_related("owner"):
        owner = business.owner
        if owner.is_staff:
            continue  # los admins crean emprendimientos "a nombre propio"; no son dueñas reales
        BusinessOwner.objects.get_or_create(user=owner, business=business, defaults={"role": "owner"})


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0001_initial"),
        ("businesses", "0004_alter_business_whatsapp"),
    ]

    operations = [
        migrations.RunPython(seed_owners, migrations.RunPython.noop),
    ]
