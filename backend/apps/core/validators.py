from django.conf import settings
from django.core.exceptions import ValidationError


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
