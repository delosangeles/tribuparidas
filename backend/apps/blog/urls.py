from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BlogCategoryViewSet,
    BlogStageViewSet,
    BlogPostViewSet,
    BlogPostCommentsView,
)

router = DefaultRouter()

router.register(
    r"blog/categories",
    BlogCategoryViewSet,
    basename="blog-category"
)

router.register(
    r"blog/stages",
    BlogStageViewSet,
    basename="blog-stage"
)

router.register(
    r"blog",
    BlogPostViewSet,
    basename="blog"
)

urlpatterns = [
    path(
        "blog/<slug:slug>/comments/",
        BlogPostCommentsView.as_view(),
        name="blog-post-comments",
    ),
    *router.urls,
]