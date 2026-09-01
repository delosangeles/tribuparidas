// Exige el código de país (ej: +57 300 000 0000); tolera espacios/guiones.
// Debe coincidir con validate_phone_with_country_code() en el backend.
export const PHONE_PATTERN = "^\\+[1-9][\\d\\s-]{6,17}$";
export const PHONE_ERROR_MESSAGE = "Escribe el número con el código de país, ej: +57 300 000 0000.";
