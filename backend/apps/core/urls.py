from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ActivityLogViewSet,
    AnalyticsSummaryView,
    FeatureFlagViewSet,
    MonthlyReportViewSet,
    PageViewCreateView,
    SiteSettingsView,
)

admin_router = DefaultRouter()
admin_router.register("admin/activity-log", ActivityLogViewSet, basename="admin-activity-log")
admin_router.register("feature-flags", FeatureFlagViewSet, basename="feature-flag")
admin_router.register("admin/reports/monthly", MonthlyReportViewSet, basename="admin-monthly-report")

urlpatterns = [
    path("site-settings/", SiteSettingsView.as_view(), name="site-settings"),
    path("analytics/pageview/", PageViewCreateView.as_view(), name="analytics-pageview"),
    path("admin/analytics/summary/", AnalyticsSummaryView.as_view(), name="admin-analytics-summary"),
    *admin_router.urls,
]
