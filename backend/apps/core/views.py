from collections import Counter
from datetime import timedelta

from django.db.models import Count
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone
from rest_framework import generics, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ActivityLog, PageView
from .permissions import IsSuperAdmin
from .serializers import ActivityLogSerializer, PageViewCreateSerializer


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/admin/activity-log/ — historial de acciones de moderación admin."""

    queryset = ActivityLog.objects.all().select_related("actor", "content_type")
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["action", "actor"]
    search_fields = ["description", "actor__email"]
    ordering_fields = ["created_at"]


class PageViewCreateView(generics.CreateAPIView):
    """POST /api/analytics/pageview/ — registra una vista de página. Público
    (hay páginas públicas como / y /login) pero guarda el usuario si hay sesión."""

    queryset = PageView.objects.all()
    serializer_class = PageViewCreateSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(user=user)


class AnalyticsSummaryView(APIView):
    """GET /api/admin/analytics/summary/ — solo Super Admin: cuándo se
    conecta la gente, qué páginas visitan y hasta dónde llegan."""

    permission_classes = [IsSuperAdmin]

    def get(self, request):
        since = timezone.now() - timedelta(days=14)
        qs = PageView.objects.filter(created_at__gte=since)

        by_day = list(
            qs.annotate(day=TruncDate("created_at")).values("day").annotate(count=Count("id")).order_by("day")
        )
        by_hour = list(
            qs.annotate(hour=ExtractHour("created_at")).values("hour").annotate(count=Count("id")).order_by("hour")
        )
        top_pages = list(qs.values("path").annotate(count=Count("id")).order_by("-count")[:10])

        # Última página vista por sesión = hasta dónde llegó esa visita.
        recent = qs.order_by("session_id", "-created_at").values("session_id", "path")
        last_page_by_session = {}
        for row in recent:
            last_page_by_session.setdefault(row["session_id"], row["path"])
        last_pages = [{"path": path, "count": count} for path, count in Counter(last_page_by_session.values()).most_common(10)]

        return Response(
            {
                "total_pageviews": qs.count(),
                "unique_sessions": qs.values("session_id").distinct().count(),
                "unique_users": qs.exclude(user__isnull=True).values("user_id").distinct().count(),
                "by_day": by_day,
                "by_hour": by_hour,
                "top_pages": top_pages,
                "last_pages": last_pages,
            }
        )
