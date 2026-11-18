import re

from django.conf import settings
from django.core.exceptions import ValidationError

PHONE_REGEX = re.compile(r"^\+[1-9]\d{6,14}$")


def validate_phone_with_country_code(value):
    """Exige el código de país (ej: +57 300 000 0000). Tolera espacios/guiones
    al escribir, pero siempre debe empezar con "+" seguido del indicativo."""
    if not value:
        return
    normalized = re.sub(r"[\s-]", "", value)
    if not PHONE_REGEX.match(normalized):
        raise ValidationError("Escribe el número con el código de país, ej: +57 300 000 0000.")


def validate_image_file(image_file):
    """Valida tamaño máximo y content-type de una imagen subida."""
    max_size_mb = getattr(settings, "MAX_IMAGE_UPLOAD_SIZE_MB", 5)
    max_size_bytes = max_size_mb * 1024 * 1024
    if image_file.size > max_size_bytes:
        raise ValidationError(f"La imagen no puede superar {max_size_mb}MB.")

    allowed_types = getattr(settings, "ALLOWED_IMAGE_CONTENT_TYPES", ["image/jpeg", "image/png", "image/webp"])
    content_type = getattr(image_file, "content_type", None)
    if content_type and content_type not in allowed_types:
        raise ValidationError("Formato de imagen no permitido. Usa JPG, PNG o WEBP.")


def validate_pdf_file(pdf_file):
    """Valida tamaño máximo, extensión y firma (%PDF) de un PDF subido."""
    max_size_mb = getattr(settings, "MAX_PDF_UPLOAD_SIZE_MB", 10)
    if pdf_file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"El PDF no puede superar {max_size_mb}MB.")
    if not str(getattr(pdf_file, "name", "")).lower().endswith(".pdf"):
        raise ValidationError("El archivo debe ser un PDF.")
    head = pdf_file.read(5)
    pdf_file.seek(0)
    if head != b"%PDF-":
        raise ValidationError("El archivo no es un PDF válido.")
