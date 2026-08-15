import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.categories.models import Category
from apps.businesses.models import Business

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return Category.objects.create(name="Repostería")


@pytest.fixture
def owner():
    return User.objects.create_user(email="owner@example.com", password="ClaveSegura123")


@pytest.fixture
def other_owner():
    return User.objects.create_user(email="other@example.com", password="ClaveSegura123")


@pytest.fixture
def api():
    return APIClient()


def test_create_business_defaults_to_pending(api, owner, category):
    api.force_authenticate(user=owner)
    response = api.post(
        "/api/my/businesses/",
        {
            "name": "Dulces de Prueba",
            "category": category.id,
            "city": "Cali",
            "department": "Valle del Cauca",
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    business = Business.objects.get(name="Dulces de Prueba")
    assert business.status == Business.Status.PENDING
    assert business.owner == owner


def test_pending_business_not_visible_in_public_list(api, owner, category):
    Business.objects.create(owner=owner, name="Negocio Pendiente", category=category, city="Cali", department="Valle")
    response = api.get("/api/businesses/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 0


def test_approved_business_visible_in_public_list(api, owner, category):
    Business.objects.create(
        owner=owner,
        name="Negocio Aprobado",
        category=category,
        city="Cali",
        department="Valle",
        status=Business.Status.APPROVED,
    )
    response = api.get("/api/businesses/")
    assert response.data["count"] == 1


def test_owner_can_update_own_business(api, owner, category):
    business = Business.objects.create(owner=owner, name="Mi Negocio", category=category, city="Cali", department="Valle")
    api.force_authenticate(user=owner)
    response = api.patch(f"/api/my/businesses/{business.id}/", {"city": "Palmira"}, format="multipart")
    assert response.status_code == status.HTTP_200_OK
    business.refresh_from_db()
    assert business.city == "Palmira"


def test_other_user_cannot_edit_business(api, owner, other_owner, category):
    business = Business.objects.create(owner=owner, name="Mi Negocio 2", category=category, city="Cali", department="Valle")
    api.force_authenticate(user=other_owner)
    response = api.patch(f"/api/my/businesses/{business.id}/", {"city": "Palmira"}, format="multipart")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    business.refresh_from_db()
    assert business.city == "Cali"


def test_admin_can_approve_business(api, owner, category):
    admin = User.objects.create_superuser(email="admin2@example.com", password="ClaveSegura123")
    business = Business.objects.create(owner=owner, name="Por Aprobar", category=category, city="Cali", department="Valle")
    api.force_authenticate(user=admin)
    response = api.patch(f"/api/admin/businesses/{business.id}/approve/")
    assert response.status_code == status.HTTP_200_OK
    business.refresh_from_db()
    assert business.status == Business.Status.APPROVED


def test_non_admin_cannot_approve_business(api, owner, category):
    business = Business.objects.create(owner=owner, name="Otro Por Aprobar", category=category, city="Cali", department="Valle")
    api.force_authenticate(user=owner)
    response = api.patch(f"/api/admin/businesses/{business.id}/approve/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
