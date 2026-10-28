const HAS_TAGS = /<\/?(p|br|strong|b|em|i|u|s|h2|h3|ul|ol|li|blockquote|a|img|hr)\b/i;

function escapeHtml(value: string) {
  return value.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Los artículos anteriores al editor son texto plano con saltos de línea;
 * los nuevos son HTML (ya sanitizado por el backend). Devuelve siempre HTML. */
export function contentToHtml(content: string): string {
  if (!content) return "";
  if (HAS_TAGS.test(content)) return content;
  return content
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, "<br>")}</p>`)
    .join("");
}
