import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin():
    return User.objects.create_superuser(email="admin@example.com", password="ClaveSegura123")


@pytest.fixture
def api():
    return APIClient()


def test_anonymous_cannot_list_categories(api):
    response = api.get("/api/categories/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logged_in_list_only_shows_top_level_categories(api):
    visitor = User.objects.create_user(email="visitante@example.com", password="ClaveSegura123")
    parent = Category.objects.create(name="Bebé")
    Category.objects.create(name="Pañales", parent=parent)
    api.force_authenticate(user=visitor)
    response = api.get("/api/categories/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "Bebé"
    assert len(response.data["results"][0]["subcategories"]) == 1


def test_admin_can_create_subcategory(api, admin):
    parent = Category.objects.create(name="Bebé")
    api.force_authenticate(user=admin)
    response = api.post("/api/categories/", {"name": "Pañales", "parent": parent.id}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["parent"] == parent.id
    assert response.data["parent_name"] == "Bebé"


def test_subcategory_cannot_have_a_subcategory_as_parent(api, admin):
    parent = Category.objects.create(name="Bebé")
    child = Category.objects.create(name="Pañales", parent=parent)
    api.force_authenticate(user=admin)
    response = api.post("/api/categories/", {"name": "Pañales Talla 1", "parent": child.id}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_category_with_subcategories_cannot_become_a_subcategory(api, admin):
    parent = Category.objects.create(name="Bebé")
    other = Category.objects.create(name="Servicios")
    Category.objects.create(name="Pañales", parent=parent)
    api.force_authenticate(user=admin)
    response = api.patch(f"/api/categories/{parent.slug}/", {"parent": other.id}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_non_admin_cannot_create_category(api):
    response = api.post("/api/categories/", {"name": "Nueva"}, format="json")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
