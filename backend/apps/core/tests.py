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
