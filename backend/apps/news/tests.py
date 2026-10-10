import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from .models import News

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin():
    return User.objects.create_user(email="admin@example.com", password="x", is_staff=True)


@pytest.fixture
def member():
    return User.objects.create_user(email="mama@example.com", password="x")


def make_news(admin, visibility, title="Noticia", **kwargs):
    now = timezone.now()
    return News.objects.create(
        title=title,
        image_desktop="news/desktop/a.png",
        image_mobile="news/mobile/a.png",
        published_at=kwargs.pop("published_at", now - timezone.timedelta(days=1)),
        expires_at=kwargs.pop("expires_at", now + timezone.timedelta(days=1)),
        visibility=visibility,
        created_by=admin,
        **kwargs,
    )


def png():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")
    return SimpleUploadedFile("a.png", buffer.getvalue(), content_type="image/png")


def payload(**extra):
    now = timezone.now()
    data = {
        "title": "Nueva",
        "published_at": now.isoformat(),
        "expires_at": (now + timezone.timedelta(days=1)).isoformat(),
        "image_desktop": png(),
        "image_mobile": png(),
    }
    data.update(extra)
    return data


def test_anonymous_sees_only_public_live_news(api, admin):
    make_news(admin, "public", title="Pública")
    make_news(admin, "private", title="Privada")
    make_news(admin, "public", title="Inactiva", is_active=False)
    make_news(admin, "public", title="Vencida", expires_at=timezone.now() - timezone.timedelta(hours=1))

    assert [n["title"] for n in api.get("/api/news/").data["results"]] == ["Pública"]
    assert [n["title"] for n in api.get("/api/news/active/").data] == ["Pública"]


def test_anonymous_cannot_open_a_private_news_detail(api, admin):
    private = make_news(admin, "private")
    public = make_news(admin, "public", title="Abierta")
    assert api.get(f"/api/news/{private.pk}/").status_code == 404
    assert api.get(f"/api/news/{public.pk}/").status_code == 200


def test_logged_in_member_sees_public_and_private(api, admin, member):
    make_news(admin, "public", title="Pública")
    make_news(admin, "private", title="Privada")
    api.force_authenticate(user=member)
    assert {n["title"] for n in api.get("/api/news/").data["results"]} == {"Pública", "Privada"}
    assert {n["title"] for n in api.get("/api/news/active/").data} == {"Pública", "Privada"}


def test_anonymous_cannot_write(api):
    assert api.post("/api/news/", {"title": "x"}).status_code == 401


def test_member_cannot_write(api, member):
    api.force_authenticate(user=member)
    assert api.post("/api/news/", {"title": "x"}).status_code == 403


def test_visibility_is_required_when_creating(api, admin):
    api.force_authenticate(user=admin)
    response = api.post("/api/news/", payload(), format="multipart")
    assert response.status_code == 400
    assert "visibility" in response.data


def test_visibility_rejects_unknown_value(api, admin):
    api.force_authenticate(user=admin)
    response = api.post("/api/news/", payload(visibility="secreta"), format="multipart")
    assert response.status_code == 400


def test_admin_creates_news_with_visibility(api, admin):
    api.force_authenticate(user=admin)
    response = api.post("/api/news/", payload(visibility="public"), format="multipart")
    assert response.status_code == 201, response.data
    assert response.data["visibility"] == "public"
