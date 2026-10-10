import type { Child, User } from "~/types";

/** Estado del formulario de datos para festejos (registro y perfil). */
export interface FestejosFormState {
  birth_date: string;
  children: Child[];
  pregnant: boolean;
  due_date: string;
}

export function emptyFestejosForm(): FestejosFormState {
  return { birth_date: "", children: [], pregnant: false, due_date: "" };
}

export function festejosFormFromUser(user: User | null): FestejosFormState {
  return {
    birth_date: user?.birth_date || "",
    children: (user?.children || []).map((c) => ({ ...c })),
    pregnant: Boolean(user?.pregnancy),
    due_date: user?.pregnancy?.due_date || "",
  };
}

/** Payload para la API; `pregnancy: null` quita el embarazo guardado. */
export function festejosPayload(form: FestejosFormState) {
  return {
    birth_date: form.birth_date || null,
    children: form.children.map((c) => ({ ...(c.id ? { id: c.id } : {}), name: c.name.trim(), birth_date: c.birth_date })),
    pregnancy: form.pregnant && form.due_date ? { due_date: form.due_date } : null,
  };
}
