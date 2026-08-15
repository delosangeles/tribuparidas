import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.businesses.models import Business
from apps.categories.models import Category
from apps.products.models import Product

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return User.objects.create_user(email="owner@example.com", password="ClaveSegura123")


@pytest.fixture
def business(owner):
    category = Category.objects.create(name="Comida")
    return Business.objects.create(
        owner=owner, name="Negocio", category=category, city="Cali", department="Valle", status=Business.Status.APPROVED
    )


@pytest.fixture
def api():
    return APIClient()


def test_owner_can_create_product(api, owner, business):
    api.force_authenticate(user=owner)
    response = api.post(
        f"/api/my/businesses/{business.id}/products/",
        {"name": "Torta", "price": "35000", "description": "Deliciosa"},
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Product.objects.filter(business=business, name="Torta").exists()


def test_other_user_cannot_create_product_for_business(api, business):
    other = User.objects.create_user(email="intruso@example.com", password="ClaveSegura123")
    api.force_authenticate(user=other)
    response = api.post(
        f"/api/my/businesses/{business.id}/products/", {"name": "Torta", "price": "35000"}, format="multipart"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_public_can_list_active_products_of_approved_business(api, business):
    Product.objects.create(business=business, name="Producto activo", price=10000, is_active=True)
    Product.objects.create(business=business, name="Producto inactivo", price=10000, is_active=False)
    response = api.get(f"/api/businesses/{business.slug}/products/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1


def test_owner_can_delete_own_product(api, owner, business):
    product = Product.objects.create(business=business, name="Para borrar", price=1000)
    api.force_authenticate(user=owner)
    response = api.delete(f"/api/my/products/{product.id}/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Product.objects.filter(id=product.id).exists()
