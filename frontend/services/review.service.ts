import type { Favorite, Paginated, Review } from "~/types";

export const reviewService = {
  listByBusiness(businessId: number, params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Review>>(`/businesses/${businessId}/reviews/`, { params });
  },
  create(businessId: number, rating: number, comment: string) {
    return useApi().post<Review>(`/businesses/${businessId}/reviews/`, { rating, comment });
  },
  myFavorites() {
    return useApi().get<Paginated<Favorite>>("/my/favorites/");
  },
  addFavorite(businessId: number) {
    return useApi().post<Favorite>(`/businesses/${businessId}/favorite/`);
  },
  removeFavorite(businessId: number) {
    return useApi().delete(`/businesses/${businessId}/favorite/`);
  },
  adminList(params: Record<string, unknown> = {}) {
    return useApi().get<Paginated<Review>>("/admin/reviews/", { params });
  },
  adminHide(reviewId: number) {
    return useApi().delete(`/admin/reviews/${reviewId}/`);
  },
  adminRestore(reviewId: number) {
    return useApi().patch(`/admin/reviews/${reviewId}/`, { is_active: true });
  },
};
