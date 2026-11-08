from apps.core.models import FeatureFlag

from .text import normalize_text

FLAG_KEY = "alimentacion_module"


def is_alimentacion_module_live():
    """El módulo puede estar desplegado pero oculto hasta la fecha que el
    Super Admin programe en /admin/lanzamiento (FeatureFlag
    "alimentacion_module"). Si el flag no existe (entorno sin migrar) se
    comporta como activo, igual que blog y festejos."""
    flag = FeatureFlag.objects.filter(key=FLAG_KEY).first()
    return flag.is_active if flag else True


def filter_recipes(qs, params):
    """Filtros del listado: q (sin tildes), edad, tipo (slugs) y sin_alergeno
    (slugs separados por coma: excluye las recetas que los contienen)."""
    q = normalize_text(params.get("q"))
    for word in q.split():
        qs = qs.filter(search_text__contains=word)
    if params.get("edad"):
        qs = qs.filter(age_range__slug=params["edad"])
    if params.get("tipo"):
        qs = qs.filter(meal_type__slug=params["tipo"])
    excluded = [s for s in (params.get("sin_alergeno") or "").split(",") if s]
    if excluded:
        qs = qs.exclude(allergens__slug__in=excluded)
    return qs.distinct()
