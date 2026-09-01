import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import ActivityLog

from .models import Notification

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api():
    return APIClient()


def test_register_creates_inactive_user_without_tokens(api):
    response = api.post(
        "/api/auth/register/",
        {
            "email": "nueva@example.com",
            "password": "ClaveSegura123",
            "first_name": "Nueva",
            "last_name": "Usuaria",
            "whatsapp": "+57 300 000 0000",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "access" not in response.data
    assert "refresh" not in response.data
    user = User.objects.get(email="nueva@example.com")
    assert user.is_active is False


def test_register_rejects_duplicate_email(api):
    User.objects.create_user(email="dup@example.com", password="ClaveSegura123")
    response = api.post(
        "/api/auth/register/",
        {"email": "dup@example.com", "password": "OtraClave123", "first_name": "A", "last_name": "B", "whatsapp": "123"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_pending_user_cannot_login(api):
    api.post(
        "/api/auth/register/",
        {
            "email": "pendiente@example.com",
            "password": "ClaveSegura123",
            "first_name": "Pendiente",
            "last_name": "Usuaria",
            "whatsapp": "+57 300 000 0000",
        },
        format="json",
    )
    response = api.post(
        "/api/auth/login/", {"email": "pendiente@example.com", "password": "ClaveSegura123"}, format="json"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_can_login_after_admin_activates_account(api):
    api.post(
        "/api/auth/register/",
        {
            "email": "aprobada@example.com",
            "password": "ClaveSegura123",
            "first_name": "Aprobada",
            "last_name": "Usuaria",
            "whatsapp": "+57 300 000 0000",
        },
        format="json",
    )
    user = User.objects.get(email="aprobada@example.com")
    user.is_active = True
    user.save(update_fields=["is_active"])

    response = api.post(
        "/api/auth/login/", {"email": "aprobada@example.com", "password": "ClaveSegura123"}, format="json"
    )
    assert response.status_code == status.HTTP_200_OK


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


def test_register_creates_admin_notification(api):
    api.post(
        "/api/auth/register/",
        {
            "email": "aviso@example.com",
            "password": "ClaveSegura123",
            "first_name": "Aviso",
            "last_name": "Prueba",
            "whatsapp": "+57 300 000 0000",
        },
        format="json",
    )
    notification = Notification.objects.get(type=Notification.Type.NEW_REGISTRATION, related_user__email="aviso@example.com")
    assert notification.is_read is False


def test_password_reset_request_creates_notification_without_revealing_existence(api):
    User.objects.create_user(email="existe@example.com", password="ClaveSegura123")

    response = api.post("/api/auth/password-reset-request/", {"email": "existe@example.com"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert Notification.objects.filter(type=Notification.Type.PASSWORD_RESET_REQUEST, related_user__email="existe@example.com").exists()

    response = api.post("/api/auth/password-reset-request/", {"email": "noexiste@example.com"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert not Notification.objects.filter(related_user__email="noexiste@example.com").exists()


def test_admin_can_reset_user_password(api):
    admin = User.objects.create_superuser(email="admin2@example.com", password="ClaveSegura123")
    user = User.objects.create_user(email="resetme@example.com", password="ViejaClave123")
    api.force_authenticate(user=admin)

    response = api.post(f"/api/admin/users/{user.id}/reset_password/")
    assert response.status_code == status.HTTP_200_OK
    new_password = response.data["new_password"]
    assert new_password

    login = api.post("/api/auth/login/", {"email": "resetme@example.com", "password": new_password}, format="json")
    assert login.status_code == status.HTTP_200_OK


def test_non_admin_cannot_reset_password(api):
    user = User.objects.create_user(email="normal@example.com", password="ClaveSegura123")
    other = User.objects.create_user(email="otro@example.com", password="ClaveSegura123")
    api.force_authenticate(user=user)
    response = api.post(f"/api/admin/users/{other.id}/reset_password/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_list_and_mark_notification_read(api):
    admin = User.objects.create_superuser(email="admin3@example.com", password="ClaveSegura123")
    notification = Notification.objects.create(type=Notification.Type.NEW_REGISTRATION, message="Prueba")
    api.force_authenticate(user=admin)

    response = api.get("/api/admin/notifications/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1

    response = api.patch(f"/api/admin/notifications/{notification.id}/", {"is_read": True}, format="json")
    assert response.status_code == status.HTTP_200_OK
    notification.refresh_from_db()
    assert notification.is_read is True


def test_super_admin_can_promote_user_to_admin(api):
    super_admin = User.objects.create_superuser(email="super@example.com", password="ClaveSegura123")
    user = User.objects.create_user(email="candidata@example.com", password="ClaveSegura123")
    api.force_authenticate(user=super_admin)

    response = api.post(f"/api/admin/users/{user.id}/set_role/", {"is_staff": True}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["role"] == "admin"
    user.refresh_from_db()
    assert user.is_staff is True
    assert user.is_superuser is False
    assert ActivityLog.objects.filter(action="user_promoted_admin", object_id=user.id).exists()


def test_regular_admin_cannot_promote_users(api):
    admin = User.objects.create_user(email="admin4@example.com", password="ClaveSegura123", is_staff=True)
    user = User.objects.create_user(email="candidata2@example.com", password="ClaveSegura123")
    api.force_authenticate(user=admin)

    response = api.post(f"/api/admin/users/{user.id}/set_role/", {"is_staff": True}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    user.refresh_from_db()
    assert user.is_staff is False


def test_super_admin_role_cannot_be_changed_via_set_role(api):
    super_admin = User.objects.create_superuser(email="super2@example.com", password="ClaveSegura123")
    other_super = User.objects.create_superuser(email="super3@example.com", password="ClaveSegura123")
    api.force_authenticate(user=super_admin)

    response = api.post(f"/api/admin/users/{other_super.id}/set_role/", {"is_staff": False}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_activity_log_records_admin_actions_and_is_admin_only(api):
    admin = User.objects.create_user(email="admin5@example.com", password="ClaveSegura123", is_staff=True)
    visitor = User.objects.create_user(email="visitante2@example.com", password="ClaveSegura123")
    target = User.objects.create_user(email="paraaprobar@example.com", password="ClaveSegura123", is_active=False)

    api.force_authenticate(user=admin)
    api.patch(f"/api/admin/users/{target.id}/", {"is_active": True}, format="json")
    assert ActivityLog.objects.filter(action="user_activated", object_id=target.id).exists()

    response = api.get("/api/admin/activity-log/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] >= 1

    api.force_authenticate(user=visitor)
    response = api.get("/api/admin/activity-log/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_change_password_requires_authentication(api):
    response = api.post("/api/me/change-password/", {"current_password": "x", "new_password": "y"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_wrong_current_password_fails(api):
    user = User.objects.create_user(email="cambio1@example.com", password="ClaveVieja123")
    api.force_authenticate(user=user)

    response = api.post(
        "/api/me/change-password/",
        {"current_password": "Incorrecta", "new_password": "ClaveNueva456"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    user.refresh_from_db()
    assert user.check_password("ClaveVieja123")


def test_change_password_success_and_can_login_with_new_password(api):
    user = User.objects.create_user(email="cambio2@example.com", password="ClaveVieja123")
    api.force_authenticate(user=user)

    response = api.post(
        "/api/me/change-password/",
        {"current_password": "ClaveVieja123", "new_password": "ClaveNueva456"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK

    login = api.post("/api/auth/login/", {"email": "cambio2@example.com", "password": "ClaveNueva456"}, format="json")
    assert login.status_code == status.HTTP_200_OK


def test_me_update_ignores_whatsapp(api):
    user = User.objects.create_user(email="cambio3@example.com", password="ClaveSegura123", whatsapp="3000000000")
    api.force_authenticate(user=user)

    response = api.patch("/api/me/", {"first_name": "Nueva", "whatsapp": "9999999999"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.first_name == "Nueva"
    assert user.whatsapp == "3000000000"


def test_super_admin_can_create_admin_user(api):
    super_admin = User.objects.create_superuser(email="super4@example.com", password="ClaveSegura123")
    api.force_authenticate(user=super_admin)

    response = api.post(
        "/api/admin/users/",
        {"email": "nuevaadmin@example.com", "first_name": "Nueva", "last_name": "Admin", "whatsapp": "3000000000", "is_staff": True},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["role"] == "admin"
    assert "new_password" in response.data

    created = User.objects.get(email="nuevaadmin@example.com")
    assert created.is_active is True
    assert created.is_staff is True
    assert created.is_superuser is False

    login = api.post("/api/auth/login/", {"email": "nuevaadmin@example.com", "password": response.data["new_password"]}, format="json")
    assert login.status_code == status.HTTP_200_OK
    assert ActivityLog.objects.filter(action="user_created_by_admin", object_id=created.id).exists()


def test_super_admin_create_user_duplicate_email_fails(api):
    User.objects.create_user(email="repetida@example.com", password="ClaveSegura123")
    super_admin = User.objects.create_superuser(email="super5@example.com", password="ClaveSegura123")
    api.force_authenticate(user=super_admin)

    response = api.post("/api/admin/users/", {"email": "repetida@example.com", "first_name": "A", "last_name": "B"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_regular_admin_cannot_create_user(api):
    admin = User.objects.create_user(email="admin6@example.com", password="ClaveSegura123", is_staff=True)
    api.force_authenticate(user=admin)

    response = api.post("/api/admin/users/", {"email": "otra@example.com", "first_name": "A", "last_name": "B"}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN
