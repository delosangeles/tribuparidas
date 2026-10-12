import type { AdminModule } from "~/types";

export interface MadrinaAccess {
  module: AdminModule;
  can_add: boolean;
  can_approve: boolean;
  can_edit: boolean;
  can_delete: boolean;
  categories: { id: number; name: string; slug: string }[];
}

export interface Madrina {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  access: MadrinaAccess[];
}

/** Lo que se envía al guardar: categorías por id (solo blog; vacío = todas). */
export interface MadrinaAccessPayload {
  module: AdminModule;
  can_add: boolean;
  can_approve: boolean;
  can_edit: boolean;
  can_delete: boolean;
  categories: number[];
}

export const madrinaService = {
  list() {
    return useApi().get<Madrina[]>("/admin/madrinas/");
  },
  save(userId: number, access: MadrinaAccessPayload[]) {
    return useApi().put<Madrina>(`/admin/madrinas/${userId}/`, { access });
  },
  remove(userId: number) {
    return useApi().delete(`/admin/madrinas/${userId}/`);
  },
};
