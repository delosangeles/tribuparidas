"""Sanitiza el HTML del editor de texto enriquecido del blog.

Solo deja pasar una lista cerrada de etiquetas y atributos; todo lo demás se
descarta (los textos se conservan, el contenido de <script>/<style> no).
"""

from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

ALLOWED_TAGS = {
    "p", "br", "strong", "b", "em", "i", "u", "s", "h2", "h3",
    "ul", "ol", "li", "blockquote", "a", "img", "hr",
}
VOID_TAGS = {"br", "img", "hr"}
DROP_CONTENT_TAGS = {"script", "style", "iframe", "object", "embed", "template"}
ALLOWED_ATTRS = {"a": {"href"}, "img": {"src", "alt"}}
LINK_SCHEMES = {"http", "https", "mailto"}
IMAGE_SCHEMES = {"http", "https"}


def _safe_url(value, schemes, allow_relative):
    value = (value or "").strip()
    if not value or any(ord(c) < 32 for c in value):
        return None
    parsed = urlparse(value)
    if parsed.scheme:
        return value if parsed.scheme.lower() in schemes else None
    if allow_relative and value.startswith("/") and not value.startswith("//"):
        return value
    return None


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.open_tags = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_CONTENT_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth or tag not in ALLOWED_TAGS:
            return

        parts = []
        for name, value in attrs:
            if name not in ALLOWED_ATTRS.get(tag, ()):
                continue
            if name == "href":
                value = _safe_url(value, LINK_SCHEMES, allow_relative=True)
            elif name == "src":
                value = _safe_url(value, IMAGE_SCHEMES, allow_relative=True)
            if value is None:
                if tag == "img" and name == "src":
                    return  # imagen sin origen válido: se descarta
                continue
            parts.append(f' {name}="{escape(value, quote=True)}"')

        if tag == "a":
            parts.append(' target="_blank" rel="noopener noreferrer"')
        if tag == "img" and not any(p.startswith(" src=") for p in parts):
            return

        self.out.append(f"<{tag}{''.join(parts)}>")
        if tag not in VOID_TAGS:
            self.open_tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID_TAGS and tag in self.open_tags:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in DROP_CONTENT_TAGS:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth or tag in VOID_TAGS or tag not in self.open_tags:
            return
        while self.open_tags:
            last = self.open_tags.pop()
            self.out.append(f"</{last}>")
            if last == tag:
                break

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(escape(data, quote=False))

    def close_all(self):
        while self.open_tags:
            self.out.append(f"</{self.open_tags.pop()}>")


def sanitize_blog_html(value):
    parser = _Sanitizer()
    parser.feed(value or "")
    parser.close()
    parser.close_all()
    return "".join(parser.out).strip()
