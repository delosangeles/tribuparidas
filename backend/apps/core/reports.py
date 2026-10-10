"""Reporte mensual de la plataforma (solo lectura). Lo usan el endpoint del
super admin y el comando `reporte_mensual`."""
import calendar
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models import Count, Q
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone

from apps.businesses.models import Business

from .models import MonthlyReport, PageView

# Login/registro y el panel admin no son "contenido": solo agregan ruido.
ANALYTICS_EXCLUDED_PATHS = Q(path__startswith="/login") | Q(path__startswith="/registro") | Q(path__startswith="/admin")


def _bounds(year: int, month: int):
    tz = timezone.get_current_timezone()
    last = calendar.monthrange(year, month)[1]
    return (
        timezone.make_aware(datetime(year, month, 1), tz),
        timezone.make_aware(datetime(year, month, last, 23, 59, 59), tz),
        last,
    )


def _totals(year: int, month: int) -> dict:
    start, end, _ = _bounds(year, month)
    User = get_user_model()
    users = User.objects.filter(created_at__range=(start, end), is_staff=False)
    businesses = Business.objects.filter(created_at__range=(start, end))
    views = PageView.objects.filter(created_at__range=(start, end)).exclude(ANALYTICS_EXCLUDED_PATHS)
    return {
        "users": users.count(),
        "users_active": users.filter(is_active=True).count(),
        "users_pending": users.filter(is_active=False).count(),
        "businesses": businesses.count(),
        "businesses_approved": businesses.filter(status="approved").count(),
        "businesses_pending": businesses.filter(status="pending").count(),
        "pageviews": views.count(),
        "sessions": views.values("session_id").distinct().count(),
        "_qs": (users, businesses, views),
    }


def monthly_report(year: int, month: int) -> dict:
    totals = _totals(year, month)
    users, businesses, views = totals.pop("_qs")
    _, _, last_day = _bounds(year, month)

    def by_day(qs):
        return {r["d"]: r["c"] for r in qs.annotate(d=TruncDate("created_at")).values("d").annotate(c=Count("id"))}

    views_day, users_day, biz_day = by_day(views), by_day(users), by_day(businesses)
    sessions_day = {
        r["d"]: r["c"]
        for r in views.annotate(d=TruncDate("created_at")).values("d").annotate(c=Count("session_id", distinct=True))
    }
    days = []
    for n in range(1, last_day + 1):
        d = date(year, month, n)
        days.append({"date": d.isoformat(), "pageviews": views_day.get(d, 0), "users": users_day.get(d, 0), "businesses": biz_day.get(d, 0)})

    best_day = None
    if views_day:
        d = max(views_day, key=views_day.get)
        top = views.annotate(d=TruncDate("created_at")).filter(d=d).values("path").annotate(c=Count("id")).order_by("-c").first()
        best_day = {
            "date": d.isoformat(),
            "pageviews": views_day[d],
            "sessions": sessions_day.get(d, 0),
            "users": users_day.get(d, 0),
            "businesses": biz_day.get(d, 0),
            "top_path": top["path"] if top else "",
            "top_path_views": top["c"] if top else 0,
        }

    hours = {r["h"]: r["c"] for r in views.annotate(h=ExtractHour("created_at")).values("h").annotate(c=Count("id"))}
    by_hour = [{"hour": h, "count": hours.get(h, 0)} for h in range(24)]
    best_hour = max(by_hour, key=lambda x: x["count"]) if hours else None

    top_pages = list(views.values("path").annotate(count=Count("id")).order_by("-count")[:8])

    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    previous = _totals(prev_year, prev_month)
    previous.pop("_qs")

    return {
        "year": year,
        "month": month,
        "totals": totals,
        "previous": previous,
        "best_day": best_day,
        "best_hour": best_hour,
        "best_registration_day": max(
            ({"date": d.isoformat(), "count": c} for d, c in users_day.items()), key=lambda x: x["count"], default=None
        ),
        "days": days,
        "by_hour": by_hour,
        "top_pages": top_pages,
    }


MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def _fecha(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{DIAS[d.weekday()]} {d.day} de {MESES[d.month - 1]}"


def _n(value: int) -> str:
    """Número con punto de miles (4.095), como se escribe en Colombia."""
    return f"{value:,}".replace(",", ".")


def _compare(current: int, previous: int, prev_label: str) -> str:
    if not previous:
        return f"No hay datos de {prev_label} para comparar."
    pct = round((current - previous) / previous * 100)
    if pct == 0:
        return f"Igual que en {prev_label} ({previous})."
    return f"{'Subió' if pct > 0 else 'Bajó'} {abs(pct)}% frente a {prev_label} ({previous})."


def build_sections(report: dict) -> list[dict]:
    """Redacta el reporte en español como lista de {title, text}."""
    t, p = report["totals"], report["previous"]
    month_name = MESES[report["month"] - 1]
    prev_month = 12 if report["month"] == 1 else report["month"] - 1
    prev = MESES[prev_month - 1]
    sections = [
        {
            "title": "Usuarias",
            "text": f"En {month_name} se registraron {t['users']} usuarias: {t['users_active']} ya están activas y "
                    f"{t['users_pending']} esperan aprobación. {_compare(t['users'], p['users'], prev)}",
        },
        {
            "title": "Emprendimientos",
            "text": f"Se crearon {t['businesses']} emprendimientos: {t['businesses_approved']} aprobados y "
                    f"{t['businesses_pending']} pendientes de revisión. {_compare(t['businesses'], p['businesses'], prev)}",
        },
        {
            "title": "Visitas",
            "text": f"El sitio tuvo {_n(t['pageviews'])} visitas a páginas en {_n(t['sessions'])} sesiones distintas "
                    f"(sin contar login, registro ni panel admin). {_compare(t['pageviews'], p['pageviews'], prev)}",
        },
    ]
    b = report["best_day"]
    if b:
        sections.append({
            "title": "Mejor día",
            "text": f"El mejor día fue el {_fecha(b['date'])}, con {_n(b['pageviews'])} visitas. "
                    + f"Ese día hubo {b['sessions']} sesiones distintas, {b['users']} registros nuevos y "
                      f"{b['businesses']} emprendimientos nuevos. La página más vista fue {b['top_path']} "
                      f"({b['top_path_views']} visitas).",
        })
    rd_ = report["best_registration_day"]
    if rd_ and (not b or rd_["date"] != b["date"]):
        sections.append({"title": "Día con más registros", "text": f"El día con más registros fue el {_fecha(rd_['date'])} ({rd_['count']})."})
    h = report["best_hour"]
    if h:
        ordered = sorted(report["by_hour"], key=lambda x: -x["count"])[:3]
        top3 = ", ".join(f"{x['hour']:02d}:00 ({x['count']})" for x in ordered)
        sections.append({
            "title": "Mejor hora",
            "text": f"La hora con más visitas fue las {h['hour']:02d}:00 (hora Colombia), con {_n(h['count'])} visitas sumadas "
                    f"en el mes. Las tres horas más activas: {top3}.",
        })
    if report["top_pages"]:
        lines = "; ".join(f"{x['path']} ({x['count']})" for x in report["top_pages"][:5])
        sections.append({"title": "Lo más visto", "text": f"Las páginas más vistas fueron: {lines}."})
    return sections


def previous_month(today: date | None = None) -> tuple[int, int]:
    today = today or timezone.localdate()
    return (today.year - 1, 12) if today.month == 1 else (today.year, today.month - 1)


def _has_data_through(year: int, month: int) -> bool:
    """¿El sitio ya tenía actividad al cierre de ese mes? Evita reportes vacíos de antes del lanzamiento."""
    _, end, _ = _bounds(year, month)
    return (
        PageView.objects.filter(created_at__lte=end).exists()
        or get_user_model().objects.filter(created_at__lte=end).exists()
    )


def generate_report(year: int, month: int) -> tuple[MonthlyReport, bool]:
    """Crea el reporte del mes si no existe. Nunca recalcula uno existente."""
    existing = MonthlyReport.objects.filter(year=year, month=month).first()
    if existing:
        return existing, False
    data = monthly_report(year, month)
    data["sections"] = build_sections(data)
    try:
        return MonthlyReport.objects.create(year=year, month=month, data=data), True
    except IntegrityError:  # otra petición lo generó al mismo tiempo
        return MonthlyReport.objects.get(year=year, month=month), False


def ensure_previous_month_report() -> MonthlyReport | None:
    """Garantiza que el reporte del mes anterior exista (el del mes en curso
    nunca se genera: el mes todavía no termina)."""
    year, month = previous_month()
    if not _has_data_through(year, month):
        return None
    return generate_report(year, month)[0]
