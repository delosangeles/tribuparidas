from datetime import date

from django.core.management.base import BaseCommand

from apps.festejos.generator import generate
from apps.festejos.logic import week_bounds


class Command(BaseCommand):
    """Genera los festejos de la semana (lunes a domingo). Idempotente: se
    puede programar con cron (ej. lunes 6am) y correr varias veces."""

    help = "Calcula los festejos de la semana que contiene --fecha (hoy por defecto)."

    def add_arguments(self, parser):
        parser.add_argument("--fecha", type=date.fromisoformat, default=None)

    def handle(self, *args, fecha, **options):
        start, end = week_bounds(fecha or date.today())
        created = generate(start, end)
        self.stdout.write(f"Semana {start} a {end}: {created} festejos nuevos.")
