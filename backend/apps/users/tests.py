from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import ActivityLog

from django.utils import timezone

from .models import Child, MemberProfile, Notification
from .serializers import OPEN_REGISTRATION_END, OPEN_REGISTRATION_START

User = get_user_model()

pytestmark = pytest.mark.django_db

OUTSIDE_LAUNCH_WINDOW = OPEN_REGISTRATION_START - timedelta(days=1)
INSIDE_LAUNCH_WINDOW = OPEN_REGISTRATION_START + timedelta(hours=1)


@pytest.fixture
def api():
    return APIClient()


def test_register_creates_inactive_user_without_tokens(api):
    with patch("apps.users.serializers.timezone.now", return_value=OUTSIDE_LAUNCH_WINDOW):
        response = api.post(
            "/api/auth/register/",
            {
                "email": "nueva@example.com",
                "password": "ClaveSegura123",
                "first_name": "Nueva",
                "last_name": "Usuaria",
                "whatsapp": "+57 300 000 0000",
                "document_id": "1000000001",
                "birth_date": "1992-05-10",
            },
            format="json",
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert "access" not in response.data
    assert "refresh" not in response.data
    user = User.objects.get(email="nueva@example.com")
    # Activa (puede iniciar sesión) pero sin aprobar hasta confirmar el grupo de WhatsApp.
    assert user.is_active is True and user.is_approved is False


def test_register_during_launch_window_is_active_immediately(api):
    with patch("apps.users.serializers.timezone.now", return_value=INSIDE_LAUNCH_WINDOW):
        response = api.post(
            "/api/auth/register/",
            {
                "email": "lanzamiento@example.com",
                "password": "ClaveSegura123",
                "first_name": "Lanzamiento",
                "last_name": "Usuaria",
                "whatsapp": "+57 300 000 0000",
                "document_id": "1000000002",
                "birth_date": "1992-05-10",
            },
            format="json",
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert "activa" in response.data["detail"]
    user = User.objects.get(email="lanzamiento@example.com")
    assert user.is_active is True and user.is_approved is True

    login = api.post("/api/auth/login/", {"email": "lanzamiento@example.com", "password": "ClaveSegura123"}, format="json")
    assert login.status_code == status.HTTP_200_OK


def test_register_after_launch_window_ends_is_pending_again(api):
    after_window = OPEN_REGISTRATION_END + timedelta(hours=1)
    with patch("apps.users.serializers.timezone.now", return_value=after_window):
        response = api.post(
            "/api/auth/register/",
            {
                "email": "tarde@example.com",
                "password": "ClaveSegura123",
                "first_name": "Tarde",
                "last_name": "Usuaria",
                "whatsapp": "+57 300 000 0000",
                "document_id": "1000000003",
                "birth_date": "1992-05-10",
            },
            format="json",
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert "grupo de WhatsApp" in response.data["detail"]
    user = User.objects.get(email="tarde@example.com")
    assert user.is_active is True and user.is_approved is False


def test_register_rejects_duplicate_email(api):
    User.objects.create_user(email="dup@example.com", password="ClaveSegura123")
    response = api.post(
        "/api/auth/register/",
        {"email": "dup@example.com", "password": "OtraClave123", "first_name": "A", "last_name": "B", "whatsapp": "123"},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def _register_outside_window(api, email="pendiente@example.com", document_id="1000000004"):
    with patch("apps.users.serializers.timezone.now", return_value=OUTSIDE_LAUNCH_WINDOW):
        return api.post(
            "/api/auth/register/",
            {
                "email": email,
                "password": "ClaveSegura123",
                "first_name": "Pendiente",
                "last_name": "Usuaria",
                "whatsapp": "+57 300 000 0000",
                "document_id": document_id,
                "birth_date": "1992-05-10",
            },
            format="json",
        )


def _login_client(api, email="pendiente@example.com"):
    """Cliente con un JWT real (force_authenticate se salta la autenticación que limita a las cuentas sin aprobar)."""
    from rest_framework.test import APIClient

    response = api.post("/api/auth/login/", {"email": email, "password": "ClaveSegura123"}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["user"]["is_approved"] is False
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def test_unapproved_user_can_log_in_but_only_sees_the_pending_notice(api):
    _register_outside_window(api)
    client = _login_client(api)
    assert client.get("/api/me/").status_code == status.HTTP_200_OK
    for path in ("/api/festejos/", "/api/my/businesses/", "/api/my/favorites/", "/api/admin/users/"):
        response = client.get(path)
        assert response.status_code == status.HTTP_403_FORBIDDEN, path
    denied = client.get("/api/my/favorites/")
    assert "grupo de WhatsApp" in str(denied.data["detail"])
    # No puede participar: escribir queda bloqueado.
    assert client.post("/api/businesses/1/favorite/").status_code == status.HTTP_403_FORBIDDEN


def test_unapproved_user_is_treated_as_visitor_on_public_reads(api):

    _register_outside_window(api)
    client = _login_client(api)
    assert client.get("/api/businesses/").status_code == status.HTTP_200_OK
    assert client.get("/api/news/").status_code == status.HTTP_200_OK  # como visitante: solo las públicas


def test_unapproved_user_can_request_access_and_admin_is_notified(api):
    _register_outside_window(api)
    client = _login_client(api)
    assert client.post("/api/me/request-access/").status_code == status.HTTP_202_ACCEPTED
    assert client.post("/api/me/request-access/").status_code == status.HTTP_202_ACCEPTED  # sin duplicar
    assert Notification.objects.filter(type="access_request", related_user__email="pendiente@example.com").count() == 1


def test_approved_user_cannot_request_access(api):
    user = User.objects.create_user(email="ok@example.com", password="x", is_approved=True)
    api.force_authenticate(user)
    assert api.post("/api/me/request-access/").status_code == status.HTTP_400_BAD_REQUEST


def test_admin_approval_opens_the_site_and_is_logged(api):
    _register_outside_window(api)
    target = User.objects.get(email="pendiente@example.com")
    admin = User.objects.create_user(email="adm-aprueba@example.com", password="x", is_staff=True)
    api.force_authenticate(admin)
    assert api.patch(f"/api/admin/users/{target.id}/", {"is_approved": True}, format="json").status_code == 200
    api.force_authenticate(None)
    client = _login_client_approved(api)
    assert client.get("/api/my/favorites/").status_code == status.HTTP_200_OK
    # ...y se puede quitar la aprobación
    api.force_authenticate(admin)
    api.patch(f"/api/admin/users/{target.id}/", {"is_approved": False}, format="json")
    assert ActivityLog.objects.filter(action="user_unapproved", object_id=target.id).exists()


def _login_client_approved(api):
    from rest_framework.test import APIClient

    response = api.post("/api/auth/login/", {"email": "pendiente@example.com", "password": "ClaveSegura123"}, format="json")
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def test_excel_users_are_active_and_approved_but_cannot_log_in_until_they_register(api):
    pending = User(email="excel2@example.com", registration_status="pending_registration", is_active=True, is_approved=True)
    pending.set_unusable_password()
    pending.save()
    response = api.post("/api/auth/login/", {"email": "excel2@example.com", "password": "loquesea"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    with patch("apps.users.serializers.timezone.now", return_value=OUTSIDE_LAUNCH_WINDOW):
        registered = api.post(
            "/api/auth/register/",
            {**REGISTER_BASE, "email": "excel2@example.com"},
            format="json",
        )
    assert registered.status_code == status.HTTP_201_CREATED
    assert "contraseña" in registered.data["detail"]
    login = api.post("/api/auth/login/", {"email": "excel2@example.com", "password": "ClaveSegura123"}, format="json")
    assert login.status_code == status.HTTP_200_OK and login.data["user"]["is_approved"] is True


def test_migration_splits_active_and_approved():
    import importlib

    from django.apps import apps as django_apps

    module = importlib.import_module("apps.users.migrations.0009_user_is_approved_alter_notification_type")
    excel = User(email="m1@example.com", registration_status="pending_registration", is_active=False, is_approved=False)
    excel.set_unusable_password()
    excel.save()
    waiting = User.objects.create_user(email="m2@example.com", password="x", is_active=False, is_approved=True)
    portal = User.objects.create_user(email="m3@example.com", password="x", is_active=False, account_type="portal")
    staff = User.objects.create_user(email="m4@example.com", password="x", is_active=False, is_staff=True)
    module.split_active_and_approved(django_apps, None)
    for obj in (excel, waiting, portal, staff):
        obj.refresh_from_db()
    assert (excel.is_active, excel.is_approved) == (True, True)
    assert (waiting.is_active, waiting.is_approved) == (True, False)
    assert (portal.is_active, portal.is_approved) == (False, False)
    assert staff.is_active is False  # los admins no se tocan


def test_user_can_login_after_admin_activates_account(api):
    api.post(
        "/api/auth/register/",
        {
            "email": "aprobada@example.com",
            "password": "ClaveSegura123",
            "first_name": "Aprobada",
            "last_name": "Usuaria",
            "whatsapp": "+57 300 000 0000",
            "document_id": "1000000005",
            "birth_date": "1992-05-10",
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
            "document_id": "1000000006",
            "birth_date": "1992-05-10",
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
    target = User.objects.create_user(email="paraaprobar@example.com", password="ClaveSegura123", is_approved=False)

    api.force_authenticate(user=admin)
    api.patch(f"/api/admin/users/{target.id}/", {"is_approved": True}, format="json")
    assert ActivityLog.objects.filter(action="user_approved", object_id=target.id).exists()

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
        {"email": "nuevaadmin@example.com", "first_name": "Nueva", "last_name": "Admin", "whatsapp": "+573000000000", "is_staff": True},
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


def test_admin_can_edit_user_info(api):
    admin = User.objects.create_user(email="admin8@example.com", password="ClaveSegura123", is_staff=True)
    target = User.objects.create_user(email="editar@example.com", password="ClaveSegura123", first_name="Vieja", whatsapp="+573000000000")
    api.force_authenticate(user=admin)

    response = api.patch(
        f"/api/admin/users/{target.id}/",
        {"first_name": "Nueva", "last_name": "Apellido", "whatsapp": "+573001112233"},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK
    target.refresh_from_db()
    assert target.first_name == "Nueva"
    assert target.last_name == "Apellido"
    assert target.whatsapp == "+573001112233"
    assert ActivityLog.objects.filter(action="user_info_updated", object_id=target.id).exists()


def test_register_rejects_phone_without_country_code(api):
    response = api.post(
        "/api/auth/register/",
        {
            "email": "sincodigo@example.com",
            "password": "ClaveSegura123",
            "first_name": "Sin",
            "last_name": "Codigo",
            "whatsapp": "3000000000",
            "document_id": "1000000007",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "whatsapp" in response.data


def test_register_accepts_phone_with_country_code(api):
    response = api.post(
        "/api/auth/register/",
        {
            "email": "concodigo@example.com",
            "password": "ClaveSegura123",
            "first_name": "Con",
            "last_name": "Codigo",
            "whatsapp": "+57 300 000 0000",
            "document_id": "1000000008",
            "birth_date": "1992-05-10",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED


# ---------- Datos de festejos (cumpleaños, hijos, embarazo) ----------

REGISTER_BASE = {
    "password": "ClaveSegura123",
    "first_name": "Madre",
    "last_name": "Prueba",
    "whatsapp": "+57 300 000 0000",
    "document_id": "1000000009",
}


def test_register_birth_date_is_optional(api):
    response = api.post("/api/auth/register/", {**REGISTER_BASE, "email": "sinfecha@example.com"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.get(email="sinfecha@example.com").birth_date is None


def test_register_saves_children_and_pregnancy(api):
    response = api.post(
        "/api/auth/register/",
        {
            **REGISTER_BASE,
            "email": "hijos@example.com",
            "birth_date": "1990-03-04",
            "children": [{"name": "Sol", "birth_date": "2025-01-10"}, {"name": "Leo", "birth_date": "2019-06-01"}],
            "pregnancy": {"due_date": (timezone.localdate() + timedelta(days=100)).isoformat()},
        },
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED
    user = User.objects.get(email="hijos@example.com")
    assert user.children.count() == 2
    assert user.pregnancy is not None


def test_register_rejects_child_without_name_or_date(api):
    response = api.post(
        "/api/auth/register/",
        {**REGISTER_BASE, "email": "mal@example.com", "birth_date": "1990-03-04", "children": [{"name": "", "birth_date": "2025-01-10"}]},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response = api.post(
        "/api/auth/register/",
        {**REGISTER_BASE, "email": "mal@example.com", "birth_date": "1990-03-04", "children": [{"name": "Sol"}]},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_register_rejects_future_child_birth_date(api):
    future = (timezone.localdate() + timedelta(days=5)).isoformat()
    response = api.post(
        "/api/auth/register/",
        {**REGISTER_BASE, "email": "futuro@example.com", "birth_date": "1990-03-04", "children": [{"name": "Sol", "birth_date": future}]},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_pending_registration_account_is_claimed_on_register(api):
    pending = User(email="excel@example.com", first_name="Excel", birth_date="1991-01-01", registration_status="pending_registration", is_active=False)
    pending.set_unusable_password()
    pending.save()
    Child.objects.create(user=pending, name="Bebé", birth_date="2026-01-01")

    with patch("apps.users.serializers.timezone.now", return_value=OUTSIDE_LAUNCH_WINDOW):
        response = api.post(
            "/api/auth/register/",
            {**REGISTER_BASE, "email": "excel@example.com", "birth_date": "1991-01-01"},
            format="json",
        )
    assert response.status_code == status.HTTP_201_CREATED
    assert User.objects.filter(email="excel@example.com").count() == 1
    pending.refresh_from_db()
    assert pending.registration_status == "registered"
    assert pending.is_active is True and pending.is_approved is True  # venía del Excel: ya estaba aprobada
    assert pending.check_password("ClaveSegura123")
    assert pending.children.count() == 1  # los hijos precargados se conservan


def test_pending_registration_account_cannot_log_in(api):
    pending = User(email="pend@example.com", registration_status="pending_registration", is_active=False)
    pending.set_unusable_password()
    pending.save()
    response = api.post("/api/auth/login/", {"email": "pend@example.com", "password": "loquesea"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_registered_email_cannot_be_registered_again(api):
    User.objects.create_user(email="ya@example.com", password="x")
    response = api.post(
        "/api/auth/register/", {**REGISTER_BASE, "email": "ya@example.com", "birth_date": "1990-03-04"}, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_me_update_replaces_children_and_reports_missing_data(api):
    user = User.objects.create_user(email="perfil@example.com", password="x", is_active=True)
    api.force_authenticate(user)
    assert api.get("/api/me/").data["missing_festejos_data"] == ["fecha de cumpleaños"]

    response = api.patch(
        "/api/me/",
        {"birth_date": "1990-05-05", "children": [{"name": "Sol", "birth_date": "2025-01-10"}]},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["missing_festejos_data"] == []
    child_id = response.data["children"][0]["id"]

    response = api.patch(
        "/api/me/",
        {"children": [{"id": child_id, "name": "Soledad", "birth_date": "2025-01-10"}, {"name": "Leo", "birth_date": "2020-02-02"}]},
        format="json",
    )
    assert [c["name"] for c in response.data["children"]] == ["Leo", "Soledad"] or len(response.data["children"]) == 2
    assert user.children.get(pk=child_id).name == "Soledad"

    response = api.patch("/api/me/", {"children": []}, format="json")
    assert user.children.count() == 0


def test_children_of_other_users_are_not_exposed_or_editable(api):
    owner = User.objects.create_user(email="due@example.com", password="x", is_active=True)
    child = Child.objects.create(user=owner, name="Privado", birth_date="2024-01-01")
    attacker = User.objects.create_user(email="otra@example.com", password="x", is_active=True)
    api.force_authenticate(attacker)
    assert api.get("/api/me/").data["children"] == []
    # Intentar "actualizar" el hijo ajeno por id crea uno nuevo propio, nunca toca el ajeno.
    api.patch("/api/me/", {"children": [{"id": child.id, "name": "Hack", "birth_date": "2024-01-01"}]}, format="json")
    child.refresh_from_db()
    assert child.name == "Privado"


# ---------- Datos de contacto, cédula, "Cuéntanos de ti" y fotos ----------

import io  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from PIL import Image  # noqa: E402


def make_png(name="foto.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (6, 6), "pink").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


@pytest.fixture
def member(db):
    return User.objects.create_user(email="mama@example.com", password="ClaveSegura123", first_name="Ana", last_name="Pérez", is_active=True)


@pytest.mark.parametrize("missing", ["first_name", "last_name", "whatsapp", "password"])
def test_register_requires_the_main_fields(api, missing):
    payload = {**REGISTER_BASE, "email": "obligatorios@example.com"}
    payload.pop(missing)
    response = api.post("/api/auth/register/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert missing in response.data


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_document_id_is_optional_when_registering(api, empty):
    payload = {**REGISTER_BASE, "email": "sincedula@example.com"}
    payload.pop("document_id")
    if empty is not None:
        payload["document_id"] = empty
    response = api.post("/api/auth/register/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert User.objects.get(email="sincedula@example.com").document_id is None


def test_two_accounts_can_register_without_document_id(api):
    for email in ("uno@example.com", "dos@example.com"):
        payload = {**REGISTER_BASE, "email": email}
        payload.pop("document_id")
        assert api.post("/api/auth/register/", payload, format="json").status_code == status.HTTP_201_CREATED


def test_register_requires_email(api):
    response = api.post("/api/auth/register/", dict(REGISTER_BASE), format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


def test_register_saves_location_and_open_answers(api):
    payload = {
        **REGISTER_BASE,
        "email": "completa@example.com",
        "address": "Calle 1 # 2-3",
        "department": "Valle del Cauca",
        "city": "Cali",
        "member_profile": {"occupation": "Diseñadora", "main_need": "Compañía", "looking_for": "Amigas"},
    }
    response = api.post("/api/auth/register/", payload, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    user = User.objects.get(email="completa@example.com")
    assert (user.address, user.department, user.city) == ("Calle 1 # 2-3", "Valle del Cauca", "Cali")
    assert user.member_profile.occupation == "Diseñadora"
    assert user.member_profile.main_need == "Compañía"


def test_document_id_is_normalized_and_unique(api):
    first = api.post("/api/auth/register/", {**REGISTER_BASE, "email": "a@example.com", "document_id": "1.234.567-8"}, format="json")
    assert first.status_code == status.HTTP_201_CREATED
    assert User.objects.get(email="a@example.com").document_id == "12345678"

    repeated = api.post("/api/auth/register/", {**REGISTER_BASE, "email": "b@example.com", "document_id": "12345678"}, format="json")
    assert repeated.status_code == status.HTTP_400_BAD_REQUEST
    assert "document_id" in repeated.data


def test_document_id_rejects_garbage(api):
    response = api.post("/api/auth/register/", {**REGISTER_BASE, "email": "c@example.com", "document_id": "12"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_accounts_without_document_id_do_not_clash(db):
    User.objects.create_user(email="x@example.com", password="x")
    User.objects.create_user(email="y@example.com", password="x")  # ambos con document_id nulo


def test_pending_account_can_be_claimed_keeping_its_document(api):
    User.objects.create(email="excel@example.com", registration_status="pending_registration", is_active=False, document_id="99887766")
    response = api.post(
        "/api/auth/register/", {**REGISTER_BASE, "email": "excel@example.com", "document_id": "99887766"}, format="json"
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data


def test_me_can_set_document_once_but_not_change_it(api, member):
    api.force_authenticate(user=member)
    assert api.patch("/api/me/", {"document_id": "55555555"}, format="json").status_code == status.HTTP_200_OK
    changed = api.patch("/api/me/", {"document_id": "66666666"}, format="json")
    assert changed.status_code == status.HTTP_400_BAD_REQUEST
    member.refresh_from_db()
    assert member.document_id == "55555555"


def test_me_updates_location_and_open_answers_partially(api, member):
    api.force_authenticate(user=member)
    api.patch("/api/me/", {"member_profile": {"occupation": "Docente"}}, format="json")
    response = api.patch("/api/me/", {"city": "Cali", "member_profile": {"suggestions": "Más talleres"}}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["city"] == "Cali"
    assert response.data["member_profile"]["occupation"] == "Docente"
    assert response.data["member_profile"]["suggestions"] == "Más talleres"


def test_user_can_upload_and_remove_profile_photo(api, member, media):
    api.force_authenticate(user=member)
    uploaded = api.post("/api/me/photo/", {"photo": make_png()}, format="multipart")
    assert uploaded.status_code == status.HTTP_200_OK, uploaded.data
    assert uploaded.data["photo"].startswith("http")
    member.refresh_from_db()
    assert member.photo.name.startswith("users/photos/") and "foto" not in member.photo.name

    removed = api.delete("/api/me/photo/")
    assert removed.data["photo"] is None
    member.refresh_from_db()
    assert not member.photo


def test_profile_photo_rejects_non_images(api, member, media):
    api.force_authenticate(user=member)
    fake = SimpleUploadedFile("x.png", b"no soy una imagen", content_type="image/png")
    assert api.post("/api/me/photo/", {"photo": fake}, format="multipart").status_code == status.HTTP_400_BAD_REQUEST


def test_photo_upload_requires_login(api):
    assert api.post("/api/me/photo/", {"photo": make_png()}, format="multipart").status_code == status.HTTP_401_UNAUTHORIZED


def test_user_uploads_photo_for_own_child_only(api, member, media):
    other = User.objects.create_user(email="otra@example.com", password="x", is_active=True)
    mine = Child.objects.create(user=member, name="Sol", birth_date="2026-07-07")
    theirs = Child.objects.create(user=other, name="Luna", birth_date="2026-07-07")
    api.force_authenticate(user=member)

    ok = api.post(f"/api/me/children/{mine.pk}/photo/", {"photo": make_png()}, format="multipart")
    assert ok.status_code == status.HTTP_200_OK, ok.data
    assert ok.data["photo"].startswith("http")
    assert api.post(f"/api/me/children/{theirs.pk}/photo/", {"photo": make_png()}, format="multipart").status_code == status.HTTP_404_NOT_FOUND

    me = api.get("/api/me/")
    assert me.data["children"][0]["photo"] is not None


def test_replacing_children_list_keeps_their_photos(api, member, media):
    child = Child.objects.create(user=member, name="Sol", birth_date="2026-07-07")
    api.force_authenticate(user=member)
    api.post(f"/api/me/children/{child.pk}/photo/", {"photo": make_png()}, format="multipart")
    api.patch("/api/me/", {"children": [{"id": child.pk, "name": "Sol María", "birth_date": "2026-07-07"}]}, format="json")
    child.refresh_from_db()
    assert child.name == "Sol María" and child.photo


def test_admin_sees_document_location_and_open_answers(api, member):
    admin = User.objects.create_user(email="admin@example.com", password="x", is_staff=True)
    member.document_id = "123123123"
    member.city = "Cali"
    member.save()
    MemberProfile.objects.create(user=member, main_need="Compañía")
    api.force_authenticate(user=admin)
    detail = api.get(f"/api/admin/users/{member.pk}/")
    assert detail.status_code == status.HTTP_200_OK
    assert detail.data["document_id"] == "123123123"
    assert detail.data["city"] == "Cali"
    assert detail.data["member_profile"]["main_need"] == "Compañía"


def test_document_id_is_never_exposed_publicly(api, member):
    member.document_id = "777888999"
    member.save()
    for url in ("/api/news/", "/api/businesses/", "/api/blog/"):
        assert "777888999" not in api.get(url).content.decode()


# ---------- Confirmar datos precargados del Excel ----------

def test_regular_user_does_not_need_confirmation(api, member):
    api.force_authenticate(user=member)
    assert api.get("/api/me/").data["needs_data_confirmation"] is False


def test_imported_user_is_asked_to_confirm_and_confirming_turns_it_off(api, member):
    member.needs_data_confirmation = True
    member.save()
    api.force_authenticate(user=member)
    assert api.get("/api/me/").data["needs_data_confirmation"] is True

    response = api.patch("/api/me/", {"first_name": "Ana María", "confirm_data": True}, format="json")
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["needs_data_confirmation"] is False
    assert response.data["first_name"] == "Ana María"
    member.refresh_from_db()
    assert member.data_confirmed_at is not None


def test_saving_without_confirm_flag_keeps_the_notice(api, member):
    member.needs_data_confirmation = True
    member.save()
    api.force_authenticate(user=member)
    api.patch("/api/me/", {"city": "Cali"}, format="json")
    member.refresh_from_db()
    assert member.needs_data_confirmation is True


def test_users_cannot_clear_the_flag_by_other_means(api, member):
    member.needs_data_confirmation = True
    member.save()
    api.force_authenticate(user=member)
    api.patch("/api/me/", {"needs_data_confirmation": False}, format="json")
    member.refresh_from_db()
    assert member.needs_data_confirmation is True


def test_login_response_includes_the_confirmation_flag(api, member):
    member.needs_data_confirmation = True
    member.save()
    response = api.post("/api/auth/login/", {"email": member.email, "password": "ClaveSegura123"}, format="json")
    assert response.data["user"]["needs_data_confirmation"] is True


def test_importer_flags_users_for_confirmation(db):
    from datetime import date

    from apps.users.importer import ParsedRow
    from apps.users.management.commands.importar_excel import Command

    row = ParsedRow(excel_row=2, email="nueva@example.com", first_name="Nueva", last_name="Mamá", birth_date=date(1990, 1, 1))
    row.profile = {"occupation": "Docente"}
    Command().apply_row(row)
    created = User.objects.get(email="nueva@example.com")
    assert created.needs_data_confirmation is True

    # una cuenta que ya existía también queda marcada, si no había confirmado antes
    existing = User.objects.create_user(email="vieja@example.com", password="x")
    again = ParsedRow(excel_row=3, email="vieja@example.com")
    again.profile = {"occupation": "Docente"}
    Command().apply_row(again)
    existing.refresh_from_db()
    assert existing.needs_data_confirmation is True


def test_importer_does_not_re_ask_those_who_already_confirmed(db):
    from django.utils import timezone

    from apps.users.importer import ParsedRow
    from apps.users.management.commands.importar_excel import Command

    user = User.objects.create_user(email="ya@example.com", password="x", data_confirmed_at=timezone.now())
    row = ParsedRow(excel_row=2, email="ya@example.com")
    row.profile = {"occupation": "Docente"}
    Command().apply_row(row)
    user.refresh_from_db()
    assert user.needs_data_confirmation is False


# ---------- Filtros rápidos del panel de usuarios ----------

def test_admin_user_filters_and_summary(api):
    from datetime import datetime

    from .models import MemberProfile

    admin = User.objects.create_user(email="adm@example.com", password="x", is_staff=True, is_active=True)
    active = User.objects.create_user(email="activa@example.com", password="x", is_active=True)
    waiting = User.objects.create_user(email="espera@example.com", password="x", is_approved=False)  # se registró, sin aprobar
    excel_only = User(email="excel@example.com", registration_status="pending_registration", is_active=True, is_approved=True)
    excel_only.set_unusable_password()
    excel_only.save()
    MemberProfile.objects.create(user=excel_only, form_submitted_at=timezone.now())
    MemberProfile.objects.create(user=active, form_submitted_at=timezone.now())  # registrada que también venía del Excel
    MemberProfile.objects.create(user=waiting)  # perfil sin marca de Excel (la creó ella)

    api.force_authenticate(admin)

    def emails(query):
        return {u["email"] for u in api.get(f"/api/admin/users/?{query}").data["results"]}

    assert emails("is_approved=false&registration_status=registered") == {"espera@example.com"}
    assert emails("registration_status=pending_registration") == {"excel@example.com"}
    assert emails("has_excel_data=true") == {"excel@example.com", "activa@example.com"}
    assert "excel@example.com" not in emails("has_excel_data=false")

    summary = api.get("/api/admin/users/summary/").data
    assert summary == {"all": 4, "active": 3, "pending_approval": 1, "unregistered": 1, "from_excel": 2}


def test_admin_user_summary_requires_admin(api):
    api.force_authenticate(User.objects.create_user(email="normal@example.com", password="x", is_active=True))
    assert api.get("/api/admin/users/summary/").status_code == 403
