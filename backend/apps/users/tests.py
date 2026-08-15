import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def test_register_creates_user_and_returns_tokens(api):
    response = api.post(
        "/api/auth/register/",
        {"email": "nueva@example.com", "password": "ClaveSegura123", "first_name": "Nueva", "last_name": "Usuaria"},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "access" in response.data
    assert "refresh" in response.data
    assert User.objects.filter(email="nueva@example.com").exists()


def test_register_rejects_duplicate_email(api):
    User.objects.create_user(email="dup@example.com", password="ClaveSegura123")
    response = api.post(
        "/api/auth/register/",
        {"email": "dup@example.com", "password": "OtraClave123", "first_name": "A", "last_name": "B"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_returns_tokens_and_user(api):
    User.objects.create_user(email="login@example.com", password="ClaveSegura123")
    response = api.post("/api/auth/login/", {"email": "login@example.com", "password": "ClaveSegura123"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["email"] == "login@example.com"


def test_login_fails_with_wrong_password(api):
    User.objects.create_user(email="login2@example.com", password="ClaveSegura123")
    response = api.post("/api/auth/login/", {"email": "login2@example.com", "password": "incorrecta"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_requires_authentication(api):
    response = api.get("/api/me/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_current_user(api):
    user = User.objects.create_user(email="me@example.com", password="ClaveSegura123", first_name="Yo")
    api.force_authenticate(user=user)
    response = api.get("/api/me/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["email"] == "me@example.com"
