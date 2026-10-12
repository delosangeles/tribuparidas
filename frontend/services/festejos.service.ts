import type { Festejo, FestejosResponse } from "~/types";
import { toFormData } from "./utils";

export type FestejosScope = "week" | "month";
export type FestejosKindFilter = "" | "mothers" | "children";

const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

export const festejosService = {
  list(params: { scope: FestejosScope; date?: string; kind?: string; approved?: boolean }) {
    return useApi().get<FestejosResponse>("/festejos/", {
      params: { scope: params.scope, date: params.date || undefined, kind: params.kind || undefined, approved: params.approved ? 1 : undefined },
    });
  },
  approve(id: number) {
    return useApi().post<Festejo>(`/festejos/${id}/approve/`);
  },
  approveAll(scope: FestejosScope, date?: string) {
    return useApi().post<{ approved: number }>("/festejos/approve_all/", { scope, date });
  },
  // Solo administradores. La imagen es opcional y se envía como multipart.
  create(payload: { user: number; child?: number | null; event_date: string; title: string; note?: string; image?: File | null }) {
    return useApi().post<Festejo>("/festejos/", toFormData({ kind: "manual", status: "approved", ...payload }), MULTIPART);
  },
  update(id: number, payload: Partial<Pick<Festejo, "event_date" | "title" | "note">> & { image?: File | null }) {
    return useApi().patch<Festejo>(`/festejos/${id}/`, toFormData(payload), MULTIPART);
  },
  remove(id: number) {
    return useApi().delete(`/festejos/${id}/`);
  },
};
