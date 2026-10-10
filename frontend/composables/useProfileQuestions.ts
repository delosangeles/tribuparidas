import type { MemberProfile, User } from "~/types";

/**
 * Preguntas abiertas del formulario "TRIBU PARIDAS Conociéndonos" (las mismas
 * del Excel de inscripción). Se usan para llenarlas en el registro y en el
 * perfil, y para mostrarlas (solo lectura) en la ficha del admin.
 */
export type ProfileQuestionKey = Exclude<keyof MemberProfile, "form_submitted_at">;

export interface ProfileQuestion {
  key: ProfileQuestionKey;
  label: string;
  long?: boolean;
  // false: solo se muestra en la ficha del admin (ej. el texto original de la
  // importación, que la usuaria reemplaza agregando a sus hijos de verdad).
  editable?: boolean;
}

export interface ProfileQuestionGroup {
  title: string;
  questions: ProfileQuestion[];
}

export const PROFILE_QUESTION_GROUPS: ProfileQuestionGroup[] = [
  {
    title: "Sobre ti",
    questions: [
      { key: "preferred_name", label: "¿Cómo prefieres que te llamemos?" },
      { key: "location", label: "Ciudad, barrio y país", editable: false },
      { key: "occupation", label: "¿A qué te dedicas?" },
      { key: "situation", label: "¿Cómo estás?" },
      { key: "interests", label: "Temas que te interesan", long: true },
    ],
  },
  {
    title: "Tu maternidad",
    questions: [
      { key: "children_text", label: "Nombre y edad de tus hijos (texto original)", long: true, editable: false },
      { key: "companions", label: "¿Quién te acompaña a maternar?" },
      { key: "main_need", label: "Lo que más necesitas como mamá", long: true },
    ],
  },
  {
    title: "Tu emprendimiento",
    questions: [
      { key: "has_business", label: "¿Tienes emprendimiento?" },
      { key: "business_description", label: "Tu emprendimiento o servicio", long: true },
      { key: "business_social", label: "Redes del emprendimiento" },
      { key: "offers_benefits", label: "¿Ofreces descuentos o beneficios a la tribu?" },
    ],
  },
  {
    title: "Tribu Paridas",
    questions: [
      { key: "how_met", label: "¿Cómo conociste Tribu Paridas?" },
      { key: "invited_by", label: "¿Quién te invitó?" },
      { key: "looking_for", label: "¿Qué quieres encontrar en la tribu?", long: true },
      { key: "desired_professional", label: "¿Qué profesional te gustaría tener en la comunidad?", long: true },
      { key: "meaning_phrase", label: "Para mí, Tribu Paridas significa...", long: true },
      { key: "spaces", label: "Espacios en los que quieres participar", long: true },
      { key: "suggestions", label: "Sugerencias", long: true },
    ],
  },
];

export const EDITABLE_PROFILE_KEYS: ProfileQuestionKey[] = PROFILE_QUESTION_GROUPS.flatMap((g) => g.questions)
  .filter((q) => q.editable !== false)
  .map((q) => q.key);

export type ProfileAboutState = Partial<Record<ProfileQuestionKey, string>>;

export function emptyProfileAbout(): ProfileAboutState {
  return Object.fromEntries(EDITABLE_PROFILE_KEYS.map((key) => [key, ""])) as ProfileAboutState;
}

export function profileAboutFromUser(user: User | null): ProfileAboutState {
  const profile = (user?.member_profile || {}) as Partial<MemberProfile>;
  return Object.fromEntries(EDITABLE_PROFILE_KEYS.map((key) => [key, (profile[key] as string) || ""])) as ProfileAboutState;
}

/** Payload de `member_profile`. En el registro (`onlyFilled`) solo viajan las respuestas escritas. */
export function profileAboutPayload(about: ProfileAboutState, onlyFilled = false) {
  const entries = Object.entries(about).map(([key, value]) => [key, (value || "").trim()] as const);
  return Object.fromEntries(onlyFilled ? entries.filter(([, value]) => value) : entries);
}
