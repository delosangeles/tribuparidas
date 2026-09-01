from rest_framework.routers import DefaultRouter

from .views import ActivityLogViewSet

admin_router = DefaultRouter()
admin_router.register("admin/activity-log", ActivityLogViewSet, basename="admin-activity-log")

urlpatterns = admin_router.urls
