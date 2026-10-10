from django.core.management.base import BaseCommand

from apps.core.reports import ensure_previous_month_report, generate_report, MESES


class Command(BaseCommand):
    """Genera y guarda el reporte mensual. Sin argumentos genera el del mes
    anterior (para programar el día 1 de cada mes). Un reporte ya generado
    nunca se vuelve a calcular: se omite.

        manage.py reporte_mensual                      # mes anterior
        manage.py reporte_mensual --anio 2026 --mes 9  # un mes puntual (relleno manual)
    """

    help = "Genera el reporte mensual del mes anterior (o de --anio/--mes) si aún no existe."

    def add_arguments(self, parser):
        parser.add_argument("--anio", type=int)
        parser.add_argument("--mes", type=int)

    def handle(self, *args, anio, mes, **options):
        if anio and mes:
            report, created = generate_report(anio, mes)
        else:
            report = ensure_previous_month_report()
            created = None
        if report is None:
            self.stdout.write("Aún no había actividad en el sitio ese mes: no se generó reporte.")
            return
        label = f"{MESES[report.month - 1]} {report.year}"
        if created is False:
            self.stdout.write(f"El reporte de {label} ya existía: no se modificó.")
            return
        self.stdout.write(f"Reporte de {label} guardado.\n")
        for s in report.data["sections"]:
            self.stdout.write(f"{s['title']}\n  {s['text']}\n")
