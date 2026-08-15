import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Crea (o deja intacto) un superusuario a partir de variables de entorno.

    Idempotente: se puede correr en cada arranque del contenedor sin fallar
    si el superusuario ya existe.
    """

    help = "Crea un superusuario desde DJANGO_SUPERUSER_EMAIL/PASSWORD si no existe."

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        first_name = os.environ.get("DJANGO_SUPERUSER_FIRST_NAME", "Admin")
        last_name = os.environ.get("DJANGO_SUPERUSER_LAST_NAME", "")

        if not email or not password:
            self.stdout.write("DJANGO_SUPERUSER_EMAIL/PASSWORD no definidos, se omite.")
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(f"Superusuario {email} ya existe.")
            return

        User.objects.create_superuser(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        self.stdout.write(self.style.SUCCESS(f"Superusuario {email} creado."))
