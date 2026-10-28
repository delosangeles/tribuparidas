from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminBenefitViewSet,
    AdminBusinessOwnerViewSet,
    AdminMembershipViewSet,
    CardVisitView,
    MyCardConsentView,
    MyCardView,
    MyNoticesReadView,
    MyNoticesView,
    PortalBenefitView,
    PortalBusinessView,
    PortalChangeLogView,
    PortalFAQViewSet,
    PortalImageViewSet,
    PortalMeView,
    PortalMembersView,
    PortalQuestionAnswerView,
    PortalQuestionListView,
    PortalRegisterView,
    PortalReviewListView,
    PortalReviewReplyView,
    PortalStatsView,
    RedeemConfirmView,
    RedeemPreviewView,
    RequestMemberConversionView,
)

admin_router = DefaultRouter()
admin_router.register("admin/business-owners", AdminBusinessOwnerViewSet, basename="admin-business-owner")
admin_router.register("admin/benefits", AdminBenefitViewSet, basename="admin-benefit")
admin_router.register("admin/memberships", AdminMembershipViewSet, basename="admin-membership")

# Los ViewSets del portal cuelgan de /portal/businesses/<business_id>/…
base = "portal/businesses/<int:business_id>"
images = PortalImageViewSet.as_view({"get": "list", "post": "create"})
image_detail = PortalImageViewSet.as_view({"patch": "partial_update", "delete": "destroy"})
image_reorder = PortalImageViewSet.as_view({"post": "reorder"})
faqs = PortalFAQViewSet.as_view({"get": "list", "post": "create"})
faq_detail = PortalFAQViewSet.as_view({"patch": "partial_update", "delete": "destroy"})
faq_reorder = PortalFAQViewSet.as_view({"post": "reorder"})

urlpatterns = [
    path("portal/me/", PortalMeView.as_view(), name="portal-me"),
    path(f"{base}/", PortalBusinessView.as_view(), name="portal-business"),
    path(f"{base}/images/", images, name="portal-images"),
    path(f"{base}/images/reorder/", image_reorder, name="portal-images-reorder"),
    path(f"{base}/images/<int:pk>/", image_detail, name="portal-image-detail"),
    path(f"{base}/reviews/", PortalReviewListView.as_view(), name="portal-reviews"),
    path(f"{base}/reviews/<int:review_id>/reply/", PortalReviewReplyView.as_view(), name="portal-review-reply"),
    path(f"{base}/questions/", PortalQuestionListView.as_view(), name="portal-questions"),
    path(f"{base}/questions/<int:question_id>/answer/", PortalQuestionAnswerView.as_view(), name="portal-question-answer"),
    path(f"{base}/faqs/", faqs, name="portal-faqs"),
    path(f"{base}/faqs/reorder/", faq_reorder, name="portal-faqs-reorder"),
    path(f"{base}/faqs/<int:pk>/", faq_detail, name="portal-faq-detail"),
    path(f"{base}/benefit/", PortalBenefitView.as_view(), name="portal-benefit"),
    path(f"{base}/changes/", PortalChangeLogView.as_view(), name="portal-changes"),
    path(f"{base}/stats/", PortalStatsView.as_view(), name="portal-stats"),
    path(f"{base}/members/", PortalMembersView.as_view(), name="portal-members"),
    path(f"{base}/redeem/preview/", RedeemPreviewView.as_view(), name="portal-redeem-preview"),
    path(f"{base}/redeem/confirm/", RedeemConfirmView.as_view(), name="portal-redeem-confirm"),
    path("me/card/", MyCardView.as_view(), name="me-card"),
    path("me/card/consent/", MyCardConsentView.as_view(), name="me-card-consent"),
    path("me/notices/", MyNoticesView.as_view(), name="me-notices"),
    path("me/notices/read/", MyNoticesReadView.as_view(), name="me-notices-read"),
    path("me/request-member-conversion/", RequestMemberConversionView.as_view(), name="me-request-conversion"),
    path("businesses/<int:business_id>/card-visit/", CardVisitView.as_view(), name="business-card-visit"),
    path("auth/register-portal/", PortalRegisterView.as_view(), name="auth-register-portal"),
    *admin_router.urls,
]
