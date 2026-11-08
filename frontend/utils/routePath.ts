/** Quita la barra final de una ruta ("/portal/registro/" → "/portal/registro"). En producción nginx
 *  agrega esa barra, y las reglas de rutas públicas/privadas deben tratar igual las dos formas. */
export function normalizePath(path: string): string {
  return path.length > 1 ? path.replace(/\/+$/, "") || "/" : path;
}

// Solo las rutas que empiezan con estos prefijos exigen sesión; el resto del sitio es público.
// /alimentacion-complementaria es público (lectura); solo sus favoritos piden sesión.
const PRIVATE_PREFIXES = ["/dashboard", "/admin", "/festejos", "/registro", "/portal", "/mi-tarjeta", "/alimentacion-complementaria/favoritos"];
// El registro de emprendedoras del portal es público (crea la cuenta y su emprendimiento en espera).
const PUBLIC_EXCEPTIONS = ["/portal/registro"];

export function isPrivatePath(path: string): boolean {
  const clean = normalizePath(path);
  if (PUBLIC_EXCEPTIONS.includes(clean)) return false;
  return PRIVATE_PREFIXES.some((prefix) => clean === prefix || clean.startsWith(`${prefix}/`));
}
