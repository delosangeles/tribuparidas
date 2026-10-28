import type {
  AdminBenefit,
  BusinessOwnerRow,
  MembershipRow,
  MemberNotice,
  MyCard,
  Paginated,
  PortalBenefit,
  PortalBusiness,
  PortalBusinessRef,
  PortalChange,
  PortalFAQ,
  PortalImage,
  PortalMember,
  PortalReview,
  PortalStats,
  Question,
  RedeemPreview,
  User,
} from "~/types";

const base = (id: number) => `/portal/businesses/${id}`;

export const portalService = {
  // ---- Portal (dueñas y vendedoras)
  mine() {
    return useApi().get<PortalBusinessRef[]>("/portal/me/");
  },
  business(id: number) {
    return useApi().get<PortalBusiness>(`${base(id)}/`);
  },
  updateBusiness(id: number, payload: Partial<PortalBusiness> | FormData) {
    return useApi().patch<PortalBusiness>(`${base(id)}/`, payload);
  },
  images(id: number) {
    return useApi().get<PortalImage[]>(`${base(id)}/images/`);
  },
  uploadImage(id: number, file: File, caption = "") {
    const form = new FormData();
    form.append("image", file);
    if (caption) form.append("caption", caption);
    return useApi().post<PortalImage>(`${base(id)}/images/`, form);
  },
  deleteImage(id: number, imageId: number) {
    return useApi().delete(`${base(id)}/images/${imageId}/`);
  },
  reorderImages(id: number, ids: number[]) {
    return useApi().post<PortalImage[]>(`${base(id)}/images/reorder/`, { ids });
  },
  reviews(id: number, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<PortalReview>>(`${base(id)}/reviews/`, { params });
  },
  reply(id: number, reviewId: number, text: string) {
    return useApi().put<PortalReview>(`${base(id)}/reviews/${reviewId}/reply/`, { text });
  },
  deleteReply(id: number, reviewId: number) {
    return useApi().delete(`${base(id)}/reviews/${reviewId}/reply/`);
  },
  questions(id: number) {
    return useApi().get<Paginated<Question>>(`${base(id)}/questions/`);
  },
  answer(id: number, questionId: number, answer: string) {
    return useApi().post<Question>(`${base(id)}/questions/${questionId}/answer/`, { answer });
  },
  faqs(id: number) {
    return useApi().get<PortalFAQ[]>(`${base(id)}/faqs/`);
  },
  createFaq(id: number, payload: { question: string; answer: string }) {
    return useApi().post<PortalFAQ>(`${base(id)}/faqs/`, payload);
  },
  updateFaq(id: number, faqId: number, payload: Partial<{ question: string; answer: string }>) {
    return useApi().patch<PortalFAQ>(`${base(id)}/faqs/${faqId}/`, payload);
  },
  deleteFaq(id: number, faqId: number) {
    return useApi().delete(`${base(id)}/faqs/${faqId}/`);
  },
  reorderFaqs(id: number, ids: number[]) {
    return useApi().post<PortalFAQ[]>(`${base(id)}/faqs/reorder/`, { ids });
  },
  benefit(id: number) {
    return useApi().get<PortalBenefit | null>(`${base(id)}/benefit/`);
  },
  saveBenefit(
    id: number,
    payload: { percentage: number; conditions: string; valid_from: string | null; valid_until: string | null }
  ) {
    return useApi().put<PortalBenefit>(`${base(id)}/benefit/`, payload);
  },
  changes(id: number) {
    return useApi().get<Paginated<PortalChange>>(`${base(id)}/changes/`);
  },
  stats(id: number) {
    return useApi().get<PortalStats>(`${base(id)}/stats/`);
  },
  members(id: number, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<PortalMember>>(`${base(id)}/members/`, { params });
  },
  redeemPreview(id: number, payload: { token?: string; code?: string }) {
    return useApi().post<RedeemPreview>(`${base(id)}/redeem/preview/`, payload);
  },
  redeemConfirm(id: number, ticket: string) {
    return useApi().post<{ detail: string; percentage: number; member: { name: string } }>(
      `${base(id)}/redeem/confirm/`,
      { ticket }
    );
  },

  // ---- Usuaria: tarjeta
  card() {
    return useApi().get<MyCard>("/me/card/");
  },
  acceptConsent() {
    return useApi().post("/me/card/consent/", { accepted: true });
  },
  revokeConsent() {
    return useApi().delete("/me/card/consent/");
  },
  notices() {
    return useApi().get<Paginated<MemberNotice>>("/me/notices/");
  },
  markNoticesRead() {
    return useApi().post("/me/notices/read/");
  },
  recordVisit(businessId: number, sessionId: string) {
    return useApi().post(`/businesses/${businessId}/card-visit/`, { session_id: sessionId });
  },

  // ---- Cuentas
  registerPortal(payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    whatsapp: string;
    business_name: string;
  }) {
    return useApi().post<{ detail: string }>("/auth/register-portal/", payload);
  },
  requestMemberConversion() {
    return useApi().post<{ detail: string }>("/me/request-member-conversion/");
  },

  // ---- Admin
  adminOwners(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<BusinessOwnerRow>>("/admin/business-owners/", { params });
  },
  adminAssign(payload: { user: number; business: number; role: "owner" | "seller" }) {
    return useApi().post<BusinessOwnerRow>("/admin/business-owners/", payload);
  },
  adminSetRole(id: number, role: "owner" | "seller") {
    return useApi().patch<BusinessOwnerRow>(`/admin/business-owners/${id}/`, { role });
  },
  adminRemove(id: number) {
    return useApi().delete(`/admin/business-owners/${id}/`);
  },
  adminBenefits(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<AdminBenefit>>("/admin/benefits/", { params });
  },
  adminApproveBenefit(id: number) {
    return useApi().post<AdminBenefit>(`/admin/benefits/${id}/approve/`);
  },
  adminRejectBenefit(id: number) {
    return useApi().post<AdminBenefit>(`/admin/benefits/${id}/reject/`);
  },
  adminMemberships(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<MembershipRow>>("/admin/memberships/", { params });
  },
  adminSetMembership(userId: number, isActive: boolean) {
    return useApi().patch<MembershipRow>(`/admin/memberships/${userId}/set/`, { is_active: isActive });
  },
  adminConvertToMember(userId: number) {
    return useApi().post<User>(`/admin/users/${userId}/convert_to_member/`);
  },
};
