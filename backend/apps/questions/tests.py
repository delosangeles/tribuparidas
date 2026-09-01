import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.businesses.models import Business
from apps.categories.models import Category
from apps.questions.models import Answer, Question

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


def test_anonymous_cannot_ask_question(api, business):
    response = api.post(f"/api/businesses/{business.id}/questions/", {"question": "¿Hola?"}, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_authenticated_user_can_ask_question(api, visitor, business):
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/businesses/{business.id}/questions/", {"question": "¿Hacen envíos?"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Question.objects.filter(business=business, user=visitor).exists()


def test_only_owner_can_answer_question(api, owner, visitor, business):
    question = Question.objects.create(business=business, user=visitor, question="¿Hola?")

    api.force_authenticate(user=visitor)
    response = api.post(f"/api/questions/{question.id}/answer/", {"answer": "No debería poder"}, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN

    api.force_authenticate(user=owner)
    response = api.post(f"/api/questions/{question.id}/answer/", {"answer": "Sí, respondo yo"}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert Answer.objects.filter(question=question, user=owner).exists()


def test_anonymous_cannot_list_questions(api, business):
    response = api.get(f"/api/businesses/{business.id}/questions/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_logged_in_user_can_list_questions_of_business(api, visitor, business):
    Question.objects.create(business=business, user=visitor, question="¿Pregunta pública?")
    api.force_authenticate(user=visitor)
    response = api.get(f"/api/businesses/{business.id}/questions/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
