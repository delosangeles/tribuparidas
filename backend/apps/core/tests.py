import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import PageView

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def test_pageview_create_allowed_anonymous(api):
    response = api.post("/api/analytics/pageview/", {"session_id": "abc123", "path": "/"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    pv = PageView.objects.get()
    assert pv.path == "/"
    assert pv.session_id == "abc123"
    assert pv.user is None


def test_pageview_create_authenticated_records_user(api):
    user = User.objects.create_user(email="visita@example.com", password="ClaveSegura123")
    api.force_authenticate(user=user)

    api.post("/api/analytics/pageview/", {"session_id": "xyz789", "path": "/emprendimientos"}, format="json")
    pv = PageView.objects.get()
    assert pv.user == user


def test_analytics_summary_requires_super_admin(api):
    admin = User.objects.create_user(email="admin7@example.com", password="ClaveSegura123", is_staff=True)
    api.force_authenticate(user=admin)

    response = api.get("/api/admin/analytics/summary/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_analytics_summary_aggregates_data(api):
    user = User.objects.create_user(email="visita2@example.com", password="ClaveSegura123")
    super_admin = User.objects.create_superuser(email="super6@example.com", password="ClaveSegura123")

    PageView.objects.create(user=user, session_id="s1", path="/")
    PageView.objects.create(user=user, session_id="s1", path="/emprendimientos")
    PageView.objects.create(session_id="s2", path="/")

    api.force_authenticate(user=super_admin)
    response = api.get("/api/admin/analytics/summary/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["total_pageviews"] == 3
    assert response.data["unique_sessions"] == 2
    assert response.data["unique_users"] == 1
    top_paths = {p["path"] for p in response.data["top_pages"]}
    assert "/" in top_paths
    last_paths = {p["path"] for p in response.data["last_pages"]}
    assert "/emprendimientos" in last_paths


# ---------- Reportes mensuales (generados una sola vez, solo Super Admin) ----------

def _seed_september():
    from datetime import datetime

    from django.contrib.auth import get_user_model
    from django.utils import timezone

    from apps.core.models import PageView

    User = get_user_model()
    tz = timezone.get_current_timezone()
    for day, hour, path in [(1, 19, "/"), (1, 19, "/"), (1, 20, "/emprendimientos"), (2, 10, "/"), (3, 11, "/login")]:
        pv = PageView.objects.create(session_id=f"s{day}{hour}", path=path)
        PageView.objects.filter(pk=pv.pk).update(created_at=timezone.make_aware(datetime(2026, 9, day, hour, 30), tz))
    u = User.objects.create_user(email="m@example.com", password="x")
    User.objects.filter(pk=u.pk).update(created_at=timezone.make_aware(datetime(2026, 9, 1, 19, 5), tz))


@pytest.mark.django_db
def test_monthly_reports_only_for_super_admin():
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    User = get_user_model()
    client = APIClient()
    assert client.get("/api/admin/reports/monthly/").status_code == 401
    client.force_authenticate(User.objects.create_user(email="a@example.com", password="x", is_staff=True))
    assert client.get("/api/admin/reports/monthly/").status_code == 403


@pytest.mark.django_db
def test_report_for_previous_month_is_generated_once_and_frozen():
    from datetime import date
    from unittest.mock import patch

    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient

    from apps.core.models import MonthlyReport, PageView
    from apps.core.reports import generate_report

    User = get_user_model()
    _seed_september()
    client = APIClient()
    client.force_authenticate(User.objects.create_superuser(email="s@example.com", password="x"))

    with patch("apps.core.reports.timezone.localdate", return_value=date(2026, 10, 1)):
        res = client.get("/api/admin/reports/monthly/")
    assert res.status_code == 200 and len(res.data) == 1
    report = res.data[0]
    assert (report["year"], report["month"]) == (2026, 9)
    data = report["data"]
    assert data["totals"]["pageviews"] == 4  # /login se excluye
    assert data["best_day"]["date"] == "2026-09-01" and data["best_day"]["pageviews"] == 3
    assert data["best_hour"]["hour"] == 19
    assert any(s["title"] == "Mejor día" and "1 de septiembre" in s["text"] for s in data["sections"])

    # Aunque lleguen más datos después, el reporte guardado no se recalcula.
    PageView.objects.create(session_id="late", path="/")
    with patch("apps.core.reports.timezone.localdate", return_value=date(2026, 10, 15)):
        client.get("/api/admin/reports/monthly/")
    assert MonthlyReport.objects.count() == 1
    assert MonthlyReport.objects.get().data["totals"]["pageviews"] == 4
    assert generate_report(2026, 9)[1] is False


@pytest.mark.django_db
def test_current_month_is_never_reported_and_empty_history_is_skipped():
    from datetime import date
    from unittest.mock import patch

    from apps.core.models import MonthlyReport
    from apps.core.reports import ensure_previous_month_report

    _seed_september()
    # En septiembre todavía no se genera el de septiembre (solo se mira el mes anterior).
    with patch("apps.core.reports.timezone.localdate", return_value=date(2026, 9, 20)):
        assert ensure_previous_month_report() is None  # agosto: sin actividad previa al sitio
    assert MonthlyReport.objects.count() == 0


def test_numbers_use_dot_thousands_without_touching_text_commas():
    from apps.core.reports import _n, build_sections

    assert _n(4095) == "4.095" and _n(950) == "950"
    totals = {"users": 1, "users_active": 1, "users_pending": 0, "businesses": 0, "businesses_approved": 0,
              "businesses_pending": 0, "pageviews": 4095, "sessions": 958}
    report = {"year": 2026, "month": 9, "totals": totals, "previous": totals, "best_day": None, "best_hour": None,
              "best_registration_day": None, "by_hour": [], "top_pages": []}
    visits = next(s for s in build_sections(report) if s["title"] == "Visitas")["text"]
    assert "4.095 visitas" in visits and "login, registro" in visits


# ---------- Ajustes generales del sitio ----------


def test_site_settings_public_read_and_admin_edit(api):
    assert api.get("/api/site-settings/").data == {"access_whatsapp": ""}
    assert api.patch("/api/site-settings/", {"access_whatsapp": "+573001234567"}, format="json").status_code == 401

    normal = User.objects.create_user(email="normal@example.com", password="x")
    api.force_authenticate(normal)
    assert api.patch("/api/site-settings/", {"access_whatsapp": "+573001234567"}, format="json").status_code == 403

    admin = User.objects.create_user(email="adm@example.com", password="x", is_staff=True)
    api.force_authenticate(admin)
    response = api.patch("/api/site-settings/", {"access_whatsapp": "+57 300 123 4567"}, format="json")
    assert response.status_code == 200 and response.data["access_whatsapp"] == "+57 300 123 4567"
    api.force_authenticate(None)
    assert api.get("/api/site-settings/").data["access_whatsapp"] == "+57 300 123 4567"
    from .models import ActivityLog

    assert ActivityLog.objects.filter(action="site_setting_changed").count() == 1


def test_site_settings_validates_phone_and_rejects_unknown_keys(api):
    admin = User.objects.create_user(email="adm@example.com", password="x", is_staff=True)
    api.force_authenticate(admin)
    assert api.patch("/api/site-settings/", {"access_whatsapp": "3001234567"}, format="json").status_code == 400
    assert api.patch("/api/site-settings/", {"otra_cosa": "x"}, format="json").status_code == 400
    # se puede vaciar
    api.patch("/api/site-settings/", {"access_whatsapp": "+573001234567"}, format="json")
    assert api.patch("/api/site-settings/", {"access_whatsapp": ""}, format="json").data["access_whatsapp"] == ""


def test_unapproved_user_can_read_site_settings():
    from rest_framework_simplejwt.tokens import RefreshToken

    user = User.objects.create_user(email="sin@example.com", password="x", is_approved=False)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    assert client.get("/api/site-settings/").status_code == 200
