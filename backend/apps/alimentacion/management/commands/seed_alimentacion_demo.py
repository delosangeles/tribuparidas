from django.core.management.base import BaseCommand

from apps.alimentacion.models import (
    AgeRange,
    FoodItem,
    GuideArticle,
    MealType,
    Recipe,
    RecipeIngredient,
    RecipeStep,
    Status,
)

PLACEHOLDER = "Texto de ejemplo sin valor informativo. Reemplazar con contenido revisado por un profesional."


class Command(BaseCommand):
    help = (
        "Crea contenido de EJEMPLO en estado borrador para probar el módulo. "
        "No contiene recomendaciones reales y nunca se publica. No usar en producción."
    )

    def handle(self, *args, **options):
        age = AgeRange.objects.order_by("order").first()
        meal = MealType.objects.order_by("order").first()
        if age is None or meal is None:
            self.stderr.write("Faltan los catálogos de edades y tipos (corre migrate).")
            return

        GuideArticle.objects.get_or_create(
            title="BORRADOR DE PRUEBA — Guía de ejemplo",
            defaults={"summary": PLACEHOLDER, "content": f"<p>{PLACEHOLDER}</p>", "status": Status.DRAFT},
        )
        recipe, created = Recipe.objects.get_or_create(
            title="BORRADOR DE PRUEBA — Receta de ejemplo",
            defaults={
                "summary": PLACEHOLDER,
                "age_range": age,
                "meal_type": meal,
                "storage_tip": PLACEHOLDER,
                "status": Status.DRAFT,
            },
        )
        if created:
            RecipeIngredient.objects.create(recipe=recipe, name="Ingrediente de ejemplo", order=0)
            RecipeStep.objects.create(recipe=recipe, text=PLACEHOLDER, order=0)
            recipe.refresh_search_text()
        FoodItem.objects.get_or_create(
            name="BORRADOR DE PRUEBA — Alimento de ejemplo",
            defaults={"how_to_offer": PLACEHOLDER, "status": Status.DRAFT},
        )
        self.stdout.write(self.style.SUCCESS("Contenido de ejemplo creado (todo en borrador)."))
