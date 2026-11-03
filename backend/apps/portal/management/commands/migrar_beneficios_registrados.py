from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.businesses.models import Business
from apps.core.models import log_activity
from apps.portal.models import BusinessBenefit
from apps.portal.services import percentage_from_text


class Command(BaseCommand):
    help = (
        "Convierte los beneficios que los emprendimientos ya tenían registrados en su perfil "
        "(tipo 'Descuento' con un único porcentaje en el detalle) en Beneficio Tribu del portal, "
        "aprobado, para que se vean con su % y se puedan aplicar con la tarjeta. No toca los que ya "
        "tienen beneficio del portal. Usa --dry-run para ver qué haría sin guardar nada."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo muestra lo que haría.")

    @transaction.atomic
    def handle(self, *args, **options):
        dry = options["dry_run"]
        todo, skipped = [], []
        candidates = Business.objects.filter(status=Business.Status.APPROVED, tribe_benefit=True).order_by("name")
        for business in candidates:
            if BusinessBenefit.objects.filter(business=business).exists():
                continue
            if business.benefit_type != Business.BenefitType.DESCUENTO:
                skipped.append((business, f"tipo '{business.get_benefit_type_display() or 'sin tipo'}' (no es descuento)"))
                continue
            percentage = percentage_from_text(business.benefit_detail)
            if percentage is None:
                skipped.append((business, "el detalle no trae un único porcentaje"))
                continue
            todo.append((business, percentage))

        self.stdout.write(f"{'SIMULACIÓN — ' if dry else ''}A migrar: {len(todo)} | Se quedan como están: {len(skipped)}")
        for business, percentage in todo:
            self.stdout.write(f"  + {business.name}: {percentage}%  «{business.benefit_detail[:70]}»")
            if not dry:
                BusinessBenefit.objects.create(
                    business=business,
                    percentage=percentage,
                    conditions=business.benefit_detail,
                    status=BusinessBenefit.Status.APPROVED,
                    reviewed_at=timezone.now(),
                )
        for business, reason in skipped:
            self.stdout.write(f"  - {business.name}: {reason}")
        if todo and not dry:
            log_activity(
                None,
                "benefits_migrated",
                f"Se migraron {len(todo)} beneficios registrados a Beneficio Tribu del portal (aprobados).",
            )
