from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminReviewViewSet, BusinessReviewsView, FavoriteToggleView, MyFavoritesListView

admin_router = DefaultRouter()
admin_router.register("admin/reviews", AdminReviewViewSet, basename="admin-review")

urlpatterns = [
    path("businesses/<int:business_id>/reviews/", BusinessReviewsView.as_view(), name="business-reviews"),
    path("businesses/<int:business_id>/favorite/", FavoriteToggleView.as_view(), name="business-favorite"),
    path("my/favorites/", MyFavoritesListView.as_view(), name="my-favorites"),
    *admin_router.urls,
]
