from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.core.models import FeatureFlag
from apps.users.models import Child

from .generator import generate
from .logic import add_months, birthday_in, birthdays, month_bounds, monthiversaries, week_bounds
from .models import Festejo

User = get_user_model()


# ---------- Lógica de fechas (sin base de datos) ----------

def test_week_runs_monday_to_sunday():
    # 2026-10-04 es domingo: la semana es 28 sep - 4 oct.
    assert week_bounds(date(2026, 10, 4)) == (date(2026, 9, 28), date(2026, 10, 4))
    # un lunes abre su propia semana
    assert week_bounds(date(2026, 10, 5)) == (date(2026, 10, 5), date(2026, 10, 11))
    assert week_bounds(date(2026, 10, 7)) == (date(2026, 10, 5), date(2026, 10, 11))


def test_month_bounds():
    assert month_bounds(date(2024, 2, 10)) == (date(2024, 2, 1), date(2024, 2, 29))
    assert month_bounds(date(2026, 9, 30)) == (date(2026, 9, 1), date(2026, 9, 30))


def test_add_months_clamps_to_last_day():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 1, 31), 3) == date(2026, 4, 30)
    assert add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert add_months(date(2025, 11, 30), 3) == date(2026, 2, 28)


def test_monthiversary_born_on_31_in_30_day_month():
    birth = date(2026, 1, 31)
    found = dict((n, d) for d, n in monthiversaries(birth, date(2026, 4, 1), date(2026, 4, 30)))
    assert found == {3: date(2026, 4, 30)}


def test_monthiversaries_only_up_to_11_months():
    birth = date(2025, 1, 15)
    months = [n for _, n in monthiversaries(birth, date(2025, 1, 1), date(2027, 1, 1))]
    assert months == list(range(1, 12))  # el mes 12 es cumpleaños, no mesversario


def test_no_monthiversary_on_birth_date_itself():
    assert monthiversaries(date(2026, 5, 10), date(2026, 5, 10), date(2026, 5, 10)) == []


def test_leap_day_birthday():
    leap = date(2020, 2, 29)
    assert birthday_in(2024, leap) == date(2024, 2, 29)
    assert birthday_in(2026, leap) == date(2026, 2, 28)
    assert birthdays(leap, date(2026, 2, 23), date(2026, 3, 1)) == [(date(2026, 2, 28), 6)]


def test_birthday_not_counted_in_birth_year():
    assert birthdays(date(2026, 3, 1), date(2026, 3, 1), date(2026, 3, 1)) == []


def test_birthday_across_year_boundary_week():
    # semana 28 dic 2026 - 3 ene 2027
    found = birthdays(date(2000, 1, 2), date(2026, 12, 28), date(2027, 1, 3))
    assert found == [(date(2027, 1, 2), 27)]


# ---------- Generación y API ----------

@pytest.fixture(autouse=True)
def activate_festejos_module(db):
    """Estos tests asumen el módulo ya lanzado; la activación programada tiene
    sus propios tests al final, donde se desactiva explícitamente."""
    FeatureFlag.objects.update_or_create(key="festejos_module", defaults={"is_forced_active": True})


pytestmark_db = pytest.mark.django_db


@pytest.fixture
def mother(db):
    return User.objects.create_user(
        email="mama@example.com", password="x", first_name="Ana", last_name="Pérez",
        is_active=True, birth_date=date(1990, 10, 6),
    )


@pytest.mark.django_db
def test_generate_creates_each_kind_once(mother):
    Child.objects.create(user=mother, name="Sol", birth_date=date(2026, 7, 7))      # 3 meses el 7 oct
    Child.objects.create(user=mother, name="Leo", birth_date=date(2020, 10, 8))     # 6 años el 8 oct
    start, end = week_bounds(date(2026, 10, 6))
    assert generate(start, end) == 3
    assert generate(start, end) == 0  # idempotente
    kinds = set(Festejo.objects.values_list("kind", flat=True))
    assert kinds == {"monthiversary", "child_birthday", "mother_birthday"}


@pytest.mark.django_db
def test_generate_skips_inactive_users(mother):
    mother.is_active = False
    mother.save()
    assert generate(date(2026, 10, 5), date(2026, 10, 11)) == 0


@pytest.mark.django_db
def test_regular_user_sees_only_approved_and_admin_sees_all(mother):
    other = User.objects.create_user(email="otra@example.com", password="x", is_active=True)
    admin = User.objects.create_user(email="admin@example.com", password="x", is_active=True, is_staff=True)
    client = APIClient()

    client.force_authenticate(other)
    res = client.get("/api/festejos/?scope=week&date=2026-10-06")
    assert res.status_code == 200 and res.data["results"] == []

    client.force_authenticate(admin)
    res = client.get("/api/festejos/?scope=week&date=2026-10-06")
    assert len(res.data["results"]) == 1  # cumpleaños de la madre, pendiente
    fid = res.data["results"][0]["id"]
    assert client.post(f"/api/festejos/{fid}/approve/").status_code == 200

    client.force_authenticate(other)
    res = client.get("/api/festejos/?scope=week&date=2026-10-06")
    assert len(res.data["results"]) == 1
    assert "birth_date" not in res.data["results"][0]


@pytest.mark.django_db
def test_week_scope_excludes_dates_outside_week(mother):
    admin = User.objects.create_user(email="admin@example.com", password="x", is_active=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)
    # cumple el 6 oct (martes); la semana siguiente no debe incluirlo, el mes sí
    assert client.get("/api/festejos/?scope=week&date=2026-10-13").data["results"] == []
    assert len(client.get("/api/festejos/?scope=month&date=2026-10-13").data["results"]) == 1


@pytest.mark.django_db
def test_non_admin_cannot_write(mother):
    client = APIClient()
    client.force_authenticate(mother)
    res = client.post("/api/festejos/", {"kind": "manual", "event_date": "2026-10-10", "user": mother.id, "title": "x"})
    assert res.status_code == 403


@pytest.mark.django_db
def test_admin_can_add_manual_edit_and_delete(mother):
    admin = User.objects.create_user(email="admin@example.com", password="x", is_active=True, is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)
    res = client.post(
        "/api/festejos/",
        {"kind": "manual", "event_date": "2026-10-10", "user": mother.id, "title": "Baby shower"},
        format="json",
    )
    assert res.status_code == 201 and res.data["is_manual"] is True
    fid = res.data["id"]
    assert client.patch(f"/api/festejos/{fid}/", {"title": "Baby shower de Ana"}, format="json").status_code == 200
    assert client.delete(f"/api/festejos/{fid}/").status_code == 204


# ---------- Activación programada (FeatureFlag "festejos_module") ----------

@pytest.fixture
def festejos_module_not_live(db):
    FeatureFlag.objects.update_or_create(key="festejos_module", defaults={"is_forced_active": False, "activate_at": None})


@pytest.mark.django_db
def test_regular_user_sees_nothing_before_the_scheduled_launch(mother, festejos_module_not_live):
    admin = User.objects.create_user(email="a@example.com", password="x", is_staff=True)
    Festejo.objects.create(kind=Festejo.Kind.MANUAL, event_date=date(2026, 10, 14), user=mother, status=Festejo.Status.APPROVED, is_manual=True)
    api = APIClient()
    api.force_authenticate(user=mother)
    response = api.get("/api/festejos/", {"date": "2026-10-14"})
    assert response.status_code == 200
    assert response.data["results"] == []
    # y no se generó nada en segundo plano
    assert Festejo.objects.filter(is_manual=False).count() == 0

    api.force_authenticate(user=admin)
    assert len(api.get("/api/festejos/", {"date": "2026-10-14"}).data["results"]) >= 1


@pytest.mark.django_db
def test_regular_user_sees_it_once_the_scheduled_date_has_passed(mother, festejos_module_not_live):
    from django.utils import timezone

    Festejo.objects.create(kind=Festejo.Kind.MANUAL, event_date=date(2026, 10, 14), user=mother, status=Festejo.Status.APPROVED, is_manual=True)
    FeatureFlag.objects.filter(key="festejos_module").update(activate_at=timezone.now() - timezone.timedelta(minutes=1))
    api = APIClient()
    api.force_authenticate(user=mother)
    assert len(api.get("/api/festejos/", {"date": "2026-10-14"}).data["results"]) == 1



# ---------- Fotos en los festejos ----------

@pytest.mark.django_db
def test_festejo_shows_child_photo_and_mother_photo(mother, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    mother.photo = "users/photos/mama.png"
    mother.save()
    child = Child.objects.create(user=mother, name="Sol", birth_date=date(2026, 7, 7), photo="users/children/sol.png")
    generate(date(2026, 10, 5), date(2026, 10, 11))
    Festejo.objects.update(status=Festejo.Status.APPROVED)

    api = APIClient()
    api.force_authenticate(user=mother)
    results = api.get("/api/festejos/", {"date": "2026-10-07"}).data["results"]
    by_kind = {r["kind"]: r for r in results}
    assert by_kind["monthiversary"]["photo"].endswith("users/children/sol.png")
    assert by_kind["mother_birthday"]["photo"].endswith("users/photos/mama.png")
    assert child.photo


@pytest.mark.django_db
def test_festejo_photo_is_null_without_pictures(mother):
    Child.objects.create(user=mother, name="Sol", birth_date=date(2026, 7, 7))
    generate(date(2026, 10, 5), date(2026, 10, 11))
    Festejo.objects.update(status=Festejo.Status.APPROVED)
    api = APIClient()
    api.force_authenticate(user=mother)
    assert all(r["photo"] is None for r in api.get("/api/festejos/", {"date": "2026-10-07"}).data["results"])
