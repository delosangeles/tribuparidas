from rest_framework import permissions, viewsets

from .models import ActivityLog
from .serializers import ActivityLogSerializer


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/admin/activity-log/ — historial de acciones de moderación admin."""

    queryset = ActivityLog.objects.all().select_related("actor", "content_type")
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["action", "actor"]
    search_fields = ["description", "actor__email"]
    ordering_fields = ["created_at"]
