import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.businesses.models import Business
from apps.categories.models import Category
from apps.reviews.models import Favorite, Review

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def owner():
    return User.objects.create_user(email="owner@example.com", password="ClaveSegura123")


@pytest.fixture
def visitor():
    return User.objects.create_user(email="visitante@example.com", password="ClaveSegura123")


@pytest.fixture
def business(owner):
    category = Category.objects.create(name="Comida")
    return Business.objects.create(
        owner=owner, name="Negocio", category=category, city="Cali", department="Valle", status=Business.Status.APPROVED
    )


@pytest.fixture
def api():
    return APIClient()


def test_user_can_create_review(api, visitor, business):
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/businesses/{business.id}/reviews/", {"rating": 5, "comment": "Excelente"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    business.refresh_from_db()
    assert float(business.average_rating) == 5.0


def test_user_cannot_review_twice(api, visitor, business):
    Review.objects.create(business=business, user=visitor, rating=4)
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/businesses/{business.id}/reviews/", {"rating": 2, "comment": "Otra vez"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_average_rating_recalculates_on_new_review(api, owner, visitor, business):
    another_visitor = User.objects.create_user(email="otra@example.com", password="ClaveSegura123")
    Review.objects.create(business=business, user=visitor, rating=4)
    Review.objects.create(business=business, user=another_visitor, rating=2)
    business.refresh_from_db()
    assert float(business.average_rating) == 3.0


def test_toggle_favorite(api, visitor, business):
    api.force_authenticate(user=visitor)

    response = api.post(f"/api/businesses/{business.id}/favorite/")
    assert response.status_code == status.HTTP_201_CREATED
    assert Favorite.objects.filter(user=visitor, business=business).exists()

    response = api.delete(f"/api/businesses/{business.id}/favorite/")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not Favorite.objects.filter(user=visitor, business=business).exists()
