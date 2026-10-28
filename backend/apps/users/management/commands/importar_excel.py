import csv
from datetime import date
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from openpyxl import load_workbook

from apps.users.importer import ParsedRow, latest_per_email, parse_row
from apps.users.models import Child, MemberProfile, Pregnancy

User = get_user_model()


class Command(BaseCommand):
    """Importa el Excel de inscripción. Por defecto es una PRUEBA: no guarda
    nada, solo muestra el resumen y escribe el reporte de filas con problemas.

        manage.py importar_excel archivo.xlsx              # prueba (no guarda)
        manage.py importar_excel archivo.xlsx --aplicar    # guarda tras confirmar

    Reglas: el correo identifica a la usuaria; las que no existen se crean como
    "pendiente de registrarse" (inactivas, sin contraseña); nunca se sobrescribe
    lo que la usuaria ya llenó; fechas dudosas se dejan vacías y se reportan."""

    help = "Importa el Excel de inscripción (prueba por defecto; --aplicar para guardar)."

    def add_arguments(self, parser):
        parser.add_argument("archivo")
        parser.add_argument("--aplicar", action="store_true", help="Guarda los cambios (pide confirmación).")
        parser.add_argument("--si", action="store_true", help="Con --aplicar, no pedir confirmación interactiva.")
        parser.add_argument("--reporte", default=".", help="Carpeta donde escribir el CSV de revisión.")

    def handle(self, *args, archivo, aplicar, si, reporte, **options):
        path = Path(archivo)
        if not path.exists():
            raise CommandError(f"No existe el archivo: {path}")
        today = timezone.localdate()

        sheet = load_workbook(path, data_only=True).active
        raw_rows = list(sheet.iter_rows(min_row=2, values_only=True))
        parsed = [parse_row(i, r, today) for i, r in enumerate(raw_rows, start=2) if any(c not in (None, "") for c in r)]
        valid = [p for p in parsed if p.email and not any(i.field == "email" or (i.level == "error" and i.field == "nombre") for i in p.issues)]
        broken = [p for p in parsed if p not in valid]
        rows = latest_per_email(valid)

        plan = [self.plan_row(p) for p in rows]
        summary = {"crear": 0, "actualizar": 0, "sin cambios": 0}
        for action, _ in plan:
            summary[action] += 1

        report_path = self.write_report(Path(reporte), parsed, today)
        self.print_summary(len(raw_rows), len(rows), len(broken), summary, parsed, report_path, aplicar)

        if not aplicar:
            self.stdout.write(self.style.WARNING("PRUEBA: no se guardó nada. Revisa el reporte y ejecuta con --aplicar."))
            return
        if not si and input("¿Guardar estos cambios? Escribe 'si' para confirmar: ").strip().lower() != "si":
            self.stdout.write("Cancelado, no se guardó nada.")
            return
        with transaction.atomic():
            for p in rows:
                self.apply_row(p)
        self.stdout.write(self.style.SUCCESS("Importación guardada."))

    # ---- plan / aplicación ----

    def plan_row(self, p: ParsedRow):
        user = User.objects.filter(email=p.email).first()
        if user is None:
            return "crear", None
        return ("actualizar" if self.changes_for(user, p) else "sin cambios"), user

    def changes_for(self, user, p: ParsedRow) -> list[str]:
        """Qué campos vacíos de una usuaria existente se llenarían."""
        changes = []
        if p.birth_date and not user.birth_date:
            changes.append("birth_date")
        if p.whatsapp and not user.whatsapp:
            changes.append("whatsapp")
        if p.children and not user.children.exists():
            changes.append("children")
        if p.due_date and not hasattr(user, "pregnancy"):
            changes.append("pregnancy")
        profile = getattr(user, "member_profile", None)
        if profile is None or any(v and not getattr(profile, k, "") for k, v in p.profile.items() if k != "form_submitted_at"):
            changes.append("member_profile")
        return changes

    def apply_row(self, p: ParsedRow):
        user = User.objects.filter(email=p.email).first()
        if user is None:
            user = User(
                email=p.email, first_name=p.first_name, last_name=p.last_name, whatsapp=p.whatsapp,
                birth_date=p.birth_date, registration_status="pending_registration", is_active=True, is_approved=True,
            )
            user.set_unusable_password()
            user.save()
        else:
            # Solo se llenan campos vacíos: nunca se pisa lo que la usuaria ya escribió.
            updates = []
            if p.birth_date and not user.birth_date:
                user.birth_date = p.birth_date
                updates.append("birth_date")
            if p.whatsapp and not user.whatsapp:
                user.whatsapp = p.whatsapp
                updates.append("whatsapp")
            if updates:
                user.save(update_fields=updates)

        if p.children and not user.children.exists():
            Child.objects.bulk_create([Child(user=user, name=c.name, birth_date=c.birth_date) for c in p.children])
        if p.due_date and not Pregnancy.objects.filter(user=user).exists():
            Pregnancy.objects.create(user=user, due_date=p.due_date)

        profile, _ = MemberProfile.objects.get_or_create(user=user)
        for key, value in p.profile.items():
            if value and not getattr(profile, key):
                setattr(profile, key, value)
        profile.save()

        # Al entrar, la persona verá el aviso "tenemos información nueva para ti".
        if not user.needs_data_confirmation and not user.data_confirmed_at:
            user.needs_data_confirmation = True
            user.save(update_fields=["needs_data_confirmation"])

    # ---- reporte ----

    def write_report(self, folder: Path, parsed: list[ParsedRow], today: date) -> Path:
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"reporte_importacion_{timezone.localtime():%Y%m%d_%H%M}.csv"
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.writer(fh)
            writer.writerow(["fila_excel", "correo", "tipo", "campo", "valor_original", "detalle"])
            for p in parsed:
                for i in p.issues:
                    writer.writerow([p.excel_row, p.email, i.level, i.field, i.original, i.detail])
        return path

    def print_summary(self, total, unique, broken, summary, parsed, report_path, aplicar):
        errors = sum(1 for p in parsed for i in p.issues if i.level == "error")
        warnings = sum(1 for p in parsed for i in p.issues if i.level == "aviso")
        w = self.stdout.write
        w("\n=== Resumen de importación ===")
        w(f"Filas leídas: {total} · correos distintos válidos: {unique} · filas inválidas (omitidas): {broken}")
        w(f"Usuarias a crear (pendientes de registrarse): {summary['crear']}")
        w(f"Usuarias existentes a completar (solo campos vacíos): {summary['actualizar']}")
        w(f"Sin cambios: {summary['sin cambios']}")
        w(f"Datos descartados (errores): {errors} · avisos para revisar: {warnings}")
        w(f"Reporte para revisar: {report_path}\n")
