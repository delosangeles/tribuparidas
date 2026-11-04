from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    BlogAuthorListView,
    BlogCategoryViewSet,
    BlogStageViewSet,
    BlogPostViewSet,
    BlogPostCommentsView,
    BlogCommentDetailView,
    BlogCommentLikeView,
    BlogContentImageUploadView,
    BlogPostLikeView,
    BlogPostReadView,
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
        "blog/upload-image/",
        BlogContentImageUploadView.as_view(),
        name="blog-upload-image",
    ),
    path("blog/authors/", BlogAuthorListView.as_view(), name="blog-authors"),
    path("blog/<slug:slug>/like/", BlogPostLikeView.as_view(), name="blog-post-like"),
    path("blog/<slug:slug>/read/", BlogPostReadView.as_view(), name="blog-post-read"),
    path(
        "blog/<slug:slug>/comments/",
        BlogPostCommentsView.as_view(),
        name="blog-post-comments",
    ),
    path(
        "blog/<slug:slug>/comments/<int:pk>/",
        BlogCommentDetailView.as_view(),
        name="blog-comment-detail",
    ),
    path(
        "blog/<slug:slug>/comments/<int:pk>/like/",
        BlogCommentLikeView.as_view(),
        name="blog-comment-like",
    ),
    *router.urls,
]