import type { Answer, Paginated, Question } from "~/types";

export const questionService = {
  listByBusiness(businessId: number, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Question>>(`/businesses/${businessId}/questions/`, { params });
  },
  ask(businessId: number, question: string) {
    return useApi().post<Question>(`/businesses/${businessId}/questions/`, { question });
  },
  myQuestions(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Question>>("/my/questions/", { params });
  },
  answer(questionId: number, answer: string) {
    return useApi().post<Answer>(`/questions/${questionId}/answer/`, { answer });
  },
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Question>>("/admin/questions/", { params });
  },
  adminHide(questionId: number) {
    return useApi().delete(`/admin/questions/${questionId}/`);
  },
  adminRestore(questionId: number) {
    return useApi().patch(`/admin/questions/${questionId}/`, { is_active: true });
  },
};
