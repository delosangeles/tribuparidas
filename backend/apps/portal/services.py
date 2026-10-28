"""Lógica del portal de emprendimientos y de la tarjeta con QR.

El token del QR se genera y se verifica solo aquí (backend). No lleva datos
personales: únicamente el id de la usuaria, firmado y con vencimiento.
"""
import secrets
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.core import signing
from django.utils import timezone

from apps.core.models import FeatureFlag

from .models import BusinessBenefit, BusinessChangeLog, BusinessOwner, CardCode, DataSharingConsent, DiscountRedemption, Membership

BOGOTA = ZoneInfo("America/Bogota")
TOKEN_TTL_SECONDS = 90
TICKET_TTL_SECONDS = 180  # tiempo para confirmar tras previsualizar
CARD_SALT = "tribu.card.v1"
TICKET_SALT = "tribu.redeem.v1"


class CardError(Exception):
    """Error de validación del QR con mensaje claro para mostrar a la dueña."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def bogota_today():
    return timezone.now().astimezone(BOGOTA).date()


def is_portal_module_live():
    """Si el flag no existe todavía, se comporta como activo (igual que blog y festejos)."""
    flag = FeatureFlag.objects.filter(key="portal_module").first()
    return flag.is_active if flag else True


# ---------- Acceso al emprendimiento ----------


def portal_membership(user, business_id):
    """Fila BusinessOwner de la usuaria para ese emprendimiento (o None).
    Es la única fuente de verdad de "este emprendimiento es suyo"."""
    if not user or not user.is_authenticated:
        return None
    return (
        BusinessOwner.objects.filter(user=user, business_id=business_id, business__status="approved")
        .select_related("business")
        .first()
    )


def log_change(business, actor, entity, action, changes=None):
    BusinessChangeLog.objects.create(
        business=business, actor=actor, entity=entity, action=action, changes=changes or {}
    )


def diff_fields(instance, new_values):
    """{campo: {from, to}} solo de lo que realmente cambia."""
    changes = {}
    for field, new in new_values.items():
        old = getattr(instance, field, None)
        if hasattr(old, "name"):  # archivos
            old = old.name
        if hasattr(new, "name"):
            new = new.name
        if str(old if old is not None else "") != str(new if new is not None else ""):
            changes[field] = {"from": None if old is None else str(old), "to": None if new is None else str(new)}
    return changes


# ---------- Membresía y elegibilidad ----------


def has_active_membership(user):
    membership = Membership.objects.filter(user=user).first()  # consulta fresca: sin caché del objeto
    return membership is None or membership.is_active


def active_consent(user):
    return DataSharingConsent.objects.filter(user=user, revoked_at__isnull=True).first()


def card_blockers(user):
    """Motivos por los que la usuaria aún no puede tener tarjeta."""
    blockers = []
    if user.account_type != "member":
        blockers.append("not_member")
    if not user.is_active or not user.is_approved:
        blockers.append("inactive")
    if not has_active_membership(user):
        blockers.append("membership_inactive")
    if not user.document_id:
        blockers.append("missing_document")
    if active_consent(user) is None:
        blockers.append("consent_required")
    return blockers


# ---------- Token y código ----------


def issue_token(user):
    return signing.TimestampSigner(salt=CARD_SALT).sign(str(user.pk))


def issue_code(user):
    """Código de 6 dígitos único entre los vigentes. Se renueva con cada token."""
    now = timezone.now()
    CardCode.objects.filter(expires_at__lt=now).delete()
    taken = set(CardCode.objects.values_list("code", flat=True))
    code = f"{secrets.randbelow(1_000_000):06d}"
    while code in taken:
        code = f"{secrets.randbelow(1_000_000):06d}"
    CardCode.objects.update_or_create(
        user=user, defaults={"code": code, "expires_at": now + timedelta(seconds=TOKEN_TTL_SECONDS)}
    )
    return code


def user_from_token(token):
    from apps.users.models import User

    try:
        raw = signing.TimestampSigner(salt=CARD_SALT).unsign(token, max_age=TOKEN_TTL_SECONDS)
    except signing.SignatureExpired:
        raise CardError("expired", "Código vencido. Pídele a la usuaria que lo renueve.")
    except signing.BadSignature:
        raise CardError("invalid", "Código no válido.")
    user = User.objects.filter(pk=raw).first()
    if user is None:
        raise CardError("invalid", "Código no válido.")
    return user


def user_from_code(code):
    from apps.users.models import User

    entry = CardCode.objects.filter(code=code).select_related("user").first()
    if entry is None:
        raise CardError("invalid", "Código no válido.")
    if entry.expires_at < timezone.now():
        raise CardError("expired", "Código vencido. Pídele a la usuaria que lo renueve.")
    return User.objects.get(pk=entry.user_id)


def resolve_user(token="", code=""):
    token = (token or "").strip()
    code = (code or "").strip()
    if token:
        return user_from_token(token)
    if code:
        return user_from_code(code)
    raise CardError("invalid", "Escanea el QR o escribe el código.")


# ---------- Canje ----------


def validate_redemption(user, business):
    """Devuelve el beneficio aplicable o lanza CardError con el motivo."""
    if user.account_type != "member" or not user.is_active or not user.is_approved:
        raise CardError("inactive_account", "Cuenta inactiva.")
    if not has_active_membership(user):
        raise CardError("membership_inactive", "Membresía inactiva.")
    if active_consent(user) is None:
        raise CardError("no_consent", "La usuaria no ha aceptado compartir sus datos con los emprendimientos.")
    today = bogota_today()
    benefit = BusinessBenefit.objects.filter(business=business).first()
    if benefit is None or not benefit.is_valid_on(today):
        raise CardError("no_benefit", "Este emprendimiento no tiene un beneficio vigente.")
    if DiscountRedemption.objects.filter(user=user, business=business, local_date=today).exists():
        raise CardError("already_used", "Descuento ya usado hoy.")
    return benefit


def make_ticket(user, business):
    return signing.TimestampSigner(salt=TICKET_SALT).sign(f"{user.pk}:{business.pk}")


def read_ticket(ticket, business):
    from apps.users.models import User

    try:
        raw = signing.TimestampSigner(salt=TICKET_SALT).unsign(ticket, max_age=TICKET_TTL_SECONDS)
    except signing.SignatureExpired:
        raise CardError("expired", "La confirmación venció. Vuelve a escanear el código.")
    except signing.BadSignature:
        raise CardError("invalid", "Confirmación no válida.")
    user_id, business_id = raw.split(":")
    if int(business_id) != business.pk:
        raise CardError("invalid", "Confirmación no válida.")
    return User.objects.get(pk=user_id)

