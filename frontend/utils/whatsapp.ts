// Enlace de WhatsApp al número que el equipo define en Admin → Ajustes.

/** Mensaje predeterminado para pedir que aprueben un emprendimiento que quedó en espera. */
export function reviewWhatsappMessage(businessName: string, personName = "", email = ""): string {
  const who = [personName.trim(), email.trim() && `(${email.trim()})`].filter(Boolean).join(" ");
  return (
    `Hola, acabo de crear mi emprendimiento «${businessName}» por el portal de Tribu Paridas. ` +
    "Quedó en espera: ¿me ayudas a aprobarlo, por favor?" +
    (who ? ` Soy ${who}.` : "")
  );
}

/** wa.me con el texto ya escrito; "" si no hay número configurado. */
export function reviewWhatsappUrl(number: string, businessName: string, personName = "", email = ""): string {
  const digits = (number || "").replace(/\D/g, "");
  if (!digits) return "";
  return `https://wa.me/${digits}?text=${encodeURIComponent(reviewWhatsappMessage(businessName, personName, email))}`;
}
