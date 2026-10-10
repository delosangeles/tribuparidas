from datetime import date, datetime
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from openpyxl import Workbook

from .importer import extract_names, parse_row, split_full_name, to_date, normalize_phone
from .models import Child, Pregnancy

User = get_user_model()
TODAY = date(2026, 10, 4)


def make_row(**kw):
    row = [None] * 27
    idx = {"timestamp": 0, "email": 1, "full_name": 2, "birth_date": 4, "phone": 6, "situation": 8,
           "children_text": 9, "child1": 10, "child2": 11, "child3": 12}
    defaults = {"timestamp": datetime(2026, 9, 1, 12), "email": "Ana@Example.com ", "full_name": "Ana María Pérez Gómez",
                "birth_date": datetime(1990, 5, 5)}
    for k, v in {**defaults, **kw}.items():
        row[idx[k]] = v
    return tuple(row)


def test_names_split_by_age_terminator():
    assert extract_names("Aylin 3 años José 8 años") == [("Aylin", 36.0), ("José", 96.0)]
    assert [n for n, _ in extract_names("Jacobo 14 Martín 4")] == ["Jacobo", "Martín"]
    assert [n for n, _ in extract_names("Sara 10 años - Juan Manuel 5 meses")] == ["Sara", "Juan Manuel"]
    assert [n for n, _ in extract_names("Samuel y Matías ")] == ["Samuel", "Matías"]
    assert extract_names("0.0") == []


def test_names_assigned_by_age_when_order_is_reversed():
    row = parse_row(2, make_row(children_text="Jacob 9 años Y Thiago 9 meses", child1=datetime(2026, 1, 7), child2=datetime(2017, 5, 17)), TODAY)
    by_name = {c.name: c.birth_date.year for c in row.children}
    assert by_name == {"Thiago": 2026, "Jacob": 2017}


def test_email_normalized_and_name_split():
    row = parse_row(2, make_row(), TODAY)
    assert row.email == "ana@example.com"
    assert (row.first_name, row.last_name) == ("Ana María", "Pérez Gómez")
    assert split_full_name("Ana") == ("Ana", "")


def test_impossible_mother_birth_year_is_dropped_and_reported():
    row = parse_row(2, make_row(birth_date=datetime(2026, 8, 15)), TODAY)
    assert row.birth_date is None
    assert any(i.field == "cumpleaños madre" and i.level == "error" for i in row.issues)


def test_future_date_becomes_pregnancy_not_child():
    row = parse_row(2, make_row(situation="Embarazada", children_text="Sol", child1=datetime(2026, 11, 8)), TODAY)
    assert row.due_date == date(2026, 11, 8) and row.children == []


def test_far_future_date_is_discarded():
    row = parse_row(2, make_row(child1=datetime(2033, 8, 16)), TODAY)
    assert row.due_date is None and row.children == []
    assert any(i.level == "error" for i in row.issues)


def test_excel_serial_number_is_converted_with_warning():
    d, note = to_date(46053.0)
    assert d == date(2026, 1, 31) and note


def test_ambiguous_text_date_is_not_guessed():
    assert to_date("05/06/2026")[0] is None
    assert to_date("25/06/2026")[0] == date(2026, 6, 25)


def test_phone_normalization():
    assert normalize_phone(3008478168.0) == ("+573008478168", None)
    assert normalize_phone("+57 300 847 8168")[0] == "+573008478168"
    assert normalize_phone("12345")[0] == ""


@pytest.fixture
def excel(tmp_path):
    wb = Workbook()
    ws = wb.active
    ws.append(["h"] * 27)
    ws.append(make_row(email="nueva@example.com", children_text="Sol 3 meses", child1=datetime(2026, 7, 7)))
    ws.append(make_row(email="existe@example.com", children_text="Leo", child1=datetime(2020, 1, 1)))
    path = tmp_path / "f.xlsx"
    wb.save(path)
    return path


@pytest.mark.django_db
def test_dry_run_saves_nothing(excel, tmp_path):
    call_command("importar_excel", str(excel), "--reporte", str(tmp_path), stdout=StringIO())
    assert User.objects.count() == 0
    assert list(tmp_path.glob("reporte_importacion_*.csv"))


@pytest.mark.django_db
def test_apply_creates_pending_and_never_overwrites(excel, tmp_path):
    existing = User.objects.create_user(email="existe@example.com", password="x", first_name="Propio", is_active=True)
    existing.birth_date = date(1985, 1, 1)
    existing.save()
    mine = Child.objects.create(user=existing, name="Mío", birth_date=date(2018, 2, 2))

    call_command("importar_excel", str(excel), "--aplicar", "--si", "--reporte", str(tmp_path), stdout=StringIO())

    new = User.objects.get(email="nueva@example.com")
    assert new.registration_status == "pending_registration" and not new.is_active and not new.has_usable_password()
    assert new.children.get().name == "Sol"

    existing.refresh_from_db()
    assert existing.first_name == "Propio" and existing.birth_date == date(1985, 1, 1)
    assert list(existing.children.values_list("name", flat=True)) == ["Mío"]  # no se tocaron sus hijos
    assert existing.registration_status == "registered" and existing.is_active


@pytest.mark.django_db
def test_apply_twice_does_not_duplicate(excel, tmp_path):
    for _ in range(2):
        call_command("importar_excel", str(excel), "--aplicar", "--si", "--reporte", str(tmp_path), stdout=StringIO())
    assert User.objects.filter(email="nueva@example.com").count() == 1
    assert Child.objects.filter(user__email="nueva@example.com").count() == 1
