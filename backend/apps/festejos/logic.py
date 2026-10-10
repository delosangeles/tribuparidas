"""Lógica de fechas de festejos, sin dependencias de Django (fácil de probar).

Reglas de borde:
- Nacidos el 29 de febrero: en años no bisiestos se celebra el 28 de febrero.
- Mesversarios: si el día no existe en el mes (nacido el 31, mes de 30 días),
  se celebra el último día de ese mes.
- La semana va de lunes a domingo.
- Mesversarios solo del mes 1 al 11; al cumplir 12 meses es cumpleaños.
"""
import calendar
from datetime import date, timedelta

MAX_MONTHIVERSARY = 11


def week_bounds(day: date) -> tuple[date, date]:
    """Lunes y domingo de la semana que contiene `day`."""
    monday = day - timedelta(days=day.weekday())
    return monday, monday + timedelta(days=6)


def month_bounds(day: date) -> tuple[date, date]:
    return day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1])


def _clamped(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def add_months(start: date, months: int) -> date:
    """Suma meses calendario recortando el día al último del mes si hace falta."""
    index = start.month - 1 + months
    return _clamped(start.year + index // 12, index % 12 + 1, start.day)


def birthday_in(year: int, birth: date) -> date:
    """Fecha en que se celebra el cumpleaños de `birth` durante `year`."""
    return _clamped(year, birth.month, birth.day)


def monthiversaries(birth: date, start: date, end: date) -> list[tuple[date, int]]:
    """(fecha, número de mes) de los mesversarios 1..11 que caen en [start, end]."""
    found = []
    for n in range(1, MAX_MONTHIVERSARY + 1):
        when = add_months(birth, n)
        if start <= when <= end:
            found.append((when, n))
    return found


def birthdays(birth: date, start: date, end: date) -> list[tuple[date, int]]:
    """(fecha, años que cumple) de los cumpleaños (≥1 año) que caen en [start, end]."""
    found = []
    for year in range(start.year, end.year + 1):
        when = birthday_in(year, birth)
        age = year - birth.year
        if age >= 1 and start <= when <= end:
            found.append((when, age))
    return found
