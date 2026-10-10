"""Importación del Excel de inscripción "TRIBU PARIDAS Conociéndonos".

Las funciones de parseo son puras (sin base de datos) para poder probarlas.
Regla general: nunca adivinar. Lo que no se puede interpretar con certeza
queda vacío y se reporta para revisión manual.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from django.utils import timezone as django_timezone
from openpyxl.utils.datetime import from_excel

MIN_BIRTH_YEAR = 1930
MIN_MOTHER_AGE = 13
MAX_DUE_DAYS = 300  # una fecha posterior a la inscripción solo es creíble hasta ~10 meses

# Posición de cada columna en el Excel (ver encabezados del formulario).
COL = {
    "timestamp": 0, "email": 1, "full_name": 2, "preferred_name": 3, "birth_date": 4, "location": 5,
    "phone": 6, "occupation": 7, "situation": 8, "children_text": 9, "child1": 10, "child2": 11,
    "child3": 12, "companions": 13, "how_met": 14, "invited_by": 15, "interests": 16, "has_business": 17,
    "business_description": 18, "business_social": 19, "offers_benefits": 20, "looking_for": 21,
    "desired_professional": 22, "meaning_phrase": 23, "spaces": 24, "main_need": 25, "suggestions": 26,
}

PROFILE_FIELDS = [
    "preferred_name", "location", "occupation", "situation", "children_text", "companions", "how_met",
    "invited_by", "interests", "has_business", "business_description", "business_social",
    "offers_benefits", "looking_for", "desired_professional", "meaning_phrase", "spaces", "main_need",
    "suggestions",
]

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PREGNANT_WORDS = ("embarazad", "gestante", "gestacion", "gestación", "por nacer", "no ha nacido", "embarazo")


@dataclass
class Issue:
    level: str  # "error" (dato descartado) | "aviso" (dato guardado, conviene revisar)
    field: str
    original: str
    detail: str


@dataclass
class ChildData:
    name: str
    birth_date: date


@dataclass
class ParsedRow:
    excel_row: int
    email: str
    first_name: str = ""
    last_name: str = ""
    whatsapp: str = ""
    birth_date: date | None = None
    children: list[ChildData] = field(default_factory=list)
    due_date: date | None = None
    profile: dict = field(default_factory=dict)
    submitted_at: datetime | None = None
    issues: list[Issue] = field(default_factory=list)


def clean(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).strip()


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


def split_full_name(full_name: str) -> tuple[str, str]:
    tokens = full_name.split()
    if not tokens:
        return "", ""
    if len(tokens) == 1:
        return tokens[0], ""
    if len(tokens) == 2:
        return tokens[0], tokens[1]
    if len(tokens) == 3:
        return tokens[0], " ".join(tokens[1:])
    return " ".join(tokens[:2]), " ".join(tokens[2:])


def normalize_phone(value) -> tuple[str, str | None]:
    """Devuelve (+57..., problema). Los celulares de Colombia traen 10 dígitos."""
    raw = clean(value)
    if not raw:
        return "", None
    digits = re.sub(r"\D", "", raw)
    if raw.startswith("+") and 7 <= len(digits) <= 15:
        return "+" + digits, None
    if len(digits) == 10 and digits.startswith("3"):
        return "+57" + digits, None
    if len(digits) == 12 and digits.startswith("57"):
        return "+" + digits, None
    return "", "Formato de celular no reconocido"


def to_date(value) -> tuple[date | None, str | None]:
    """Convierte la celda a fecha. Devuelve (fecha, nota) donde nota explica
    una conversión que conviene revisar, o la causa de que no se pudo."""
    if value is None or clean(value) == "":
        return None, None
    if isinstance(value, datetime):
        return value.date(), None
    if isinstance(value, date):
        return value, None
    if isinstance(value, (int, float)):
        try:
            return from_excel(value).date(), "La celda era un número de Excel; se convirtió a fecha."
        except (ValueError, OverflowError):
            return None, "Número que no corresponde a una fecha."
    text = clean(value)
    m = re.fullmatch(r"(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})", text)
    if m:
        d, mo, y = int(m[1]), int(m[2]), int(m[3])
        if mo > 12 and d <= 12:
            return None, "Fecha ambigua (día/mes invertidos)."
        if d <= 12 and mo <= 12 and d != mo:
            return None, "Fecha ambigua: no se sabe si es día/mes o mes/día."
        try:
            return date(y, mo, d), None
        except ValueError:
            return None, "Fecha inexistente."
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        try:
            return date(int(m[1]), int(m[2]), int(m[3])), None
        except ValueError:
            return None, "Fecha inexistente."
    return None, "Texto que no se pudo interpretar como fecha."


def mentions_pregnancy(*texts: str) -> bool:
    joined = strip_accents(" ".join(texts).lower())
    return any(strip_accents(w) in joined for w in PREGNANT_WORDS)


NUMBER_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(a[ñn]os?|a|meses|mes|m|semanas|d[ií]as|d)?(?![\wáéíóúñ])", re.IGNORECASE)
SEPARATOR_RE = re.compile(r"[\n;/,.&]| y | e | - |-", re.IGNORECASE)
NOISE_RE = re.compile(
    r"(?i)\b(mam[aá]|madre|de nacid[oa]s?|cumple|el pr[oó]ximo|cron[oó]logic[oa]|corregid[oa]s?|actualmente|ya casi|medio)\b"
)


def _months(number: str, unit: str | None) -> float | None:
    value = float(number.replace(",", "."))
    unit = (unit or "").lower()
    if unit.startswith("m") and unit != "":
        return value
    if unit.startswith("s"):
        return value / 4.345
    if unit.startswith("d"):
        return value / 30.4
    # años, "a" o número suelto (se asume años si es plausible)
    return value * 12 if value <= 25 else None


def extract_names(text: str) -> list[tuple[str, float | None]]:
    """Intenta sacar (nombre, edad en meses) de cada hijo del texto libre.
    Cada edad cierra un nombre ("Aylin 3 años José 8 años" -> Aylin, José)."""
    text = clean(text)
    if not text or text in {"0", "0.0"}:
        return []
    pieces: list[tuple[str, float | None]] = []
    pos = 0
    for m in NUMBER_RE.finditer(text):
        pieces.append((text[pos:m.start()], _months(m[1], m[2])))
        pos = m.end()
    pieces.append((text[pos:], None))

    results = []
    for piece, age in pieces:
        names = []
        for seg in SEPARATOR_RE.split(NOISE_RE.sub(" ", piece)):
            seg = " ".join(seg.strip(" .,:()-").split())
            if seg and re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{2}", seg) and len(seg.split()) <= 4:
                names.append(seg)
        for i, name in enumerate(names):
            results.append((name, age if i == len(names) - 1 else None))
    return results


def assign_names(names: list[tuple[str, float | None]], dates: list[date], today: date) -> list[str]:
    """Asigna un nombre a cada fecha; por edad si todas la traen, si no por orden.
    Si no coincide la cantidad, deja nombres vacíos (se completan a mano)."""
    if len(names) != len(dates):
        return [""] * len(dates)
    if all(age is not None for _, age in names):
        remaining = list(names)
        assigned = []
        for d in dates:
            months = (today.year - d.year) * 12 + (today.month - d.month)
            best = min(remaining, key=lambda n: abs(n[1] - months))
            remaining.remove(best)
            assigned.append(best[0])
        return assigned
    return [n for n, _ in names]


def parse_row(excel_row: int, row: tuple, today: date) -> ParsedRow:
    def cell(key):
        idx = COL[key]
        return row[idx] if idx < len(row) else None

    email = clean(cell("email")).lower()
    parsed = ParsedRow(excel_row=excel_row, email=email)
    ts = cell("timestamp")
    parsed.submitted_at = ts if isinstance(ts, datetime) else None
    submitted = parsed.submitted_at.date() if parsed.submitted_at else today

    def issue(level, field_name, original, detail):
        parsed.issues.append(Issue(level, field_name, clean(original), detail))

    if not EMAIL_RE.match(email):
        issue("error", "email", email, "Correo inválido; la fila no se puede importar.")
        return parsed

    parsed.first_name, parsed.last_name = split_full_name(clean(cell("full_name")))
    if not parsed.first_name:
        issue("error", "nombre", "", "Falta el nombre completo.")

    phone, problem = normalize_phone(cell("phone"))
    parsed.whatsapp = phone
    if problem:
        issue("aviso", "celular", cell("phone"), problem)

    parsed.profile = {key: clean(cell(key)) for key in PROFILE_FIELDS}
    parsed.profile["form_submitted_at"] = (
        django_timezone.make_aware(parsed.submitted_at) if parsed.submitted_at and parsed.submitted_at.tzinfo is None else parsed.submitted_at
    )

    # Cumpleaños de la madre
    raw_birth = cell("birth_date")
    birth, note = to_date(raw_birth)
    if birth is None:
        issue("error", "cumpleaños madre", raw_birth, note or "Falta la fecha de cumpleaños.")
    elif birth.year < MIN_BIRTH_YEAR or birth > submitted - timedelta(days=365 * MIN_MOTHER_AGE):
        issue("error", "cumpleaños madre", raw_birth, f"Año imposible ({birth.year}); se dejó vacío para que la corrija.")
    else:
        parsed.birth_date = birth
        if note:
            issue("aviso", "cumpleaños madre", raw_birth, note)

    # Hijos y embarazo (hij@ 1, 2, 3)
    situation, children_text = clean(cell("situation")), clean(cell("children_text"))
    pregnant_hint = mentions_pregnancy(situation, children_text)
    child_dates: list[date] = []
    for key in ("child1", "child2", "child3"):
        raw = cell(key)
        d, note = to_date(raw)
        if d is None:
            if clean(raw):
                issue("error", f"fecha {key}", raw, note or "Fecha no interpretable.")
            continue
        if note:
            issue("aviso", f"fecha {key}", raw, note)
        if d.year < MIN_BIRTH_YEAR:
            issue("error", f"fecha {key}", raw, "Fecha imposible; se descartó.")
        elif d > submitted:
            # Posterior a la inscripción: fecha probable de parto.
            if (d - submitted).days > MAX_DUE_DAYS:
                issue("error", f"fecha {key}", raw, "Fecha futura demasiado lejana para ser un parto; se descartó.")
            elif parsed.due_date is not None:
                issue("error", f"fecha {key}", raw, "Ya hay un embarazo registrado; esta fecha futura se descartó.")
            elif d >= today:
                parsed.due_date = d
                if not pregnant_hint:
                    issue("aviso", f"fecha {key}", raw, "Fecha futura en una usuaria que no marcó embarazo; se guardó como fecha probable de parto.")
            else:
                # La fecha probable ya pasó: lo más probable es que el bebé nació.
                child_dates.append(d)
                issue("aviso", f"fecha {key}", raw, "Era fecha probable de parto y ya pasó; se guardó como nacimiento, confirmar.")
        else:
            child_dates.append(d)

    names = assign_names(extract_names(children_text), child_dates, today)
    for name, d in zip(names, child_dates):
        parsed.children.append(ChildData(name=name, birth_date=d))
    if child_dates and not any(names):
        issue("aviso", "nombres de hijos", children_text, "No se pudieron identificar los nombres; quedan por completar.")
    elif child_dates and len(extract_names(children_text)) != len(child_dates):
        issue("aviso", "nombres de hijos", children_text, "La cantidad de nombres no coincide con las fechas; nombres por completar.")
    if re.search(r"(?i)fallecid|estrella", children_text + " " + situation):
        issue("aviso", "pérdida", children_text or situation, "Menciona un bebé fallecido: revisar con sensibilidad antes de enviar festejos.")

    return parsed


def latest_per_email(rows: list[ParsedRow]) -> list[ParsedRow]:
    """Si un correo llenó el formulario varias veces se toma la respuesta más reciente."""
    by_email: dict[str, list[ParsedRow]] = {}
    for r in rows:
        by_email.setdefault(r.email, []).append(r)
    chosen = []
    for email, group in by_email.items():
        group.sort(key=lambda r: (r.submitted_at or datetime.min, r.excel_row))
        last = group[-1]
        if len(group) > 1:
            last.issues.append(
                Issue("aviso", "duplicado", email, f"Correo repetido en las filas {[g.excel_row for g in group]}; se usó la más reciente (fila {last.excel_row}).")
            )
        chosen.append(last)
    return chosen
