import unicodedata


def normalize_text(value):
    """Minúsculas y sin tildes, para buscar sin distinguir acentos."""
    decomposed = unicodedata.normalize("NFD", str(value or ""))
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower().strip()
