import type { Festejo, FestejosResponse } from "~/types";

export type FestejosScope = "week" | "month";
export type FestejosKindFilter = "" | "mothers" | "children";

export const festejosService = {
  list(params: { scope: FestejosScope; date?: string; kind?: FestejosKindFilter }) {
    return useApi().get<FestejosResponse>("/festejos/", {
      params: { scope: params.scope, date: params.date || undefined, kind: params.kind || undefined },
    });
  },
  approve(id: number) {
    return useApi().post<Festejo>(`/festejos/${id}/approve/`);
  },
  approveAll(scope: FestejosScope, date?: string) {
    return useApi().post<{ approved: number }>("/festejos/approve_all/", { scope, date });
  },
  create(payload: { user: number; child?: number | null; event_date: string; title: string; note?: string }) {
    return useApi().post<Festejo>("/festejos/", { kind: "manual", status: "approved", ...payload });
  },
  update(id: number, payload: Partial<Pick<Festejo, "event_date" | "title" | "note">>) {
    return useApi().patch<Festejo>(`/festejos/${id}/`, payload);
  },
  remove(id: number) {
    return useApi().delete(`/festejos/${id}/`);
  },
};
