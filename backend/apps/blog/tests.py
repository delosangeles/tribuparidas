import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.models import ActivityLog, FeatureFlag

from .models import BlogCategory, BlogComment, BlogPost, BlogStage

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def activate_blog_module():
    """El resto de estos tests asume el estado "ya lanzado" (como el resto
    del sitio); la activación programada tiene su propia clase de tests más
    abajo, donde la desactivan explícitamente."""
    FeatureFlag.objects.update_or_create(
        key="blog_module", defaults={"is_forced_active": True}
    )


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def admin():
    return User.objects.create_superuser(email="admin@example.com", password="ClaveSegura123", is_staff=True)


@pytest.fixture
def visitor():
    return User.objects.create_user(email="visitante@example.com", password="ClaveSegura123")


@pytest.fixture
def category():
    return BlogCategory.objects.create(name="Categoría de prueba", slug="categoria-de-prueba")


@pytest.fixture
def stage():
    return BlogStage.objects.create(name="Etapa de prueba", slug="etapa-de-prueba")


def create_payload(category, **overrides):
    payload = {
        "title": "Un artículo de prueba",
        "slug": "un-articulo-de-prueba",
        "summary": "Resumen",
        "content": "Contenido",
        "category": category.id,
        "reading_time": 3,
    }
    payload.update(overrides)
    return payload


def test_regular_user_post_goes_into_review_ignoring_sent_status_and_author(api, visitor, admin, category):
    api.force_authenticate(user=visitor)
    response = api.post(
        "/api/blog/",
        create_payload(category, status=BlogPost.Status.PUBLISHED, author=admin.id),
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    post = BlogPost.objects.get(slug="un-articulo-de-prueba")
    assert post.status == BlogPost.Status.IN_REVIEW
    assert post.author == visitor


def test_admin_can_create_published_post_and_choose_author(api, admin, visitor, category):
    api.force_authenticate(user=admin)
    response = api.post(
        "/api/blog/",
        create_payload(category, status=BlogPost.Status.PUBLISHED, author=visitor.id),
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED
    post = BlogPost.objects.get(slug="un-articulo-de-prueba")
    assert post.status == BlogPost.Status.PUBLISHED
    assert post.author == visitor


def test_regular_user_cannot_update_or_delete_a_post(api, visitor, admin, category):
    post = BlogPost.objects.create(
        title="Post existente",
        slug="post-existente",
        summary="r",
        content="c",
        category=category,
        author=admin,
        status=BlogPost.Status.PUBLISHED,
        publication_date=timezone.now(),
    )
    api.force_authenticate(user=visitor)

    update = api.patch(f"/api/blog/{post.slug}/", {"title": "hackeado"}, format="multipart")
    assert update.status_code == status.HTTP_403_FORBIDDEN

    delete = api.delete(f"/api/blog/{post.slug}/")
    assert delete.status_code == status.HTTP_403_FORBIDDEN


def test_regular_user_cannot_see_posts_in_review(api, visitor, admin, category):
    BlogPost.objects.create(
        title="En revisión",
        slug="en-revision",
        summary="r",
        content="c",
        category=category,
        author=visitor,
        status=BlogPost.Status.IN_REVIEW,
    )
    api.force_authenticate(user=visitor)
    response = api.get("/api/blog/")
    assert response.data["count"] == 0


def test_admin_can_approve_a_post_in_review(api, admin, visitor, category):
    post = BlogPost.objects.create(
        title="Pendiente de aprobar",
        slug="pendiente-de-aprobar",
        summary="r",
        content="c",
        category=category,
        author=visitor,
        status=BlogPost.Status.IN_REVIEW,
    )
    api.force_authenticate(user=admin)
    response = api.post(f"/api/blog/{post.slug}/approve/")
    assert response.status_code == status.HTTP_200_OK

    post.refresh_from_db()
    assert post.status == BlogPost.Status.PUBLISHED
    assert post.publication_date is not None
    assert ActivityLog.objects.filter(action="blog_post_approved", object_id=post.id).exists()


def test_regular_user_cannot_approve_a_post(api, visitor, category):
    post = BlogPost.objects.create(
        title="Pendiente de aprobar",
        slug="pendiente-de-aprobar",
        summary="r",
        content="c",
        category=category,
        author=visitor,
        status=BlogPost.Status.IN_REVIEW,
    )
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/blog/{post.slug}/approve/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_can_reject_a_post_in_review(api, admin, visitor, category):
    post = BlogPost.objects.create(
        title="Pendiente de rechazar",
        slug="pendiente-de-rechazar",
        summary="r",
        content="c",
        category=category,
        author=visitor,
        status=BlogPost.Status.IN_REVIEW,
    )
    api.force_authenticate(user=admin)
    response = api.post(f"/api/blog/{post.slug}/reject/")
    assert response.status_code == status.HTTP_200_OK

    post.refresh_from_db()
    assert post.status == BlogPost.Status.DRAFT
    assert ActivityLog.objects.filter(action="blog_post_rejected", object_id=post.id).exists()


def test_regular_user_cannot_reject_a_post(api, visitor, category):
    post = BlogPost.objects.create(
        title="Pendiente de rechazar",
        slug="pendiente-de-rechazar",
        summary="r",
        content="c",
        category=category,
        author=visitor,
        status=BlogPost.Status.IN_REVIEW,
    )
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/blog/{post.slug}/reject/")
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_serializer_reports_comment_count(api, admin, published_post):
    BlogComment.objects.create(post=published_post, author=admin, content="Uno")
    BlogComment.objects.create(post=published_post, author=admin, content="Dos")

    api.force_authenticate(user=admin)
    response = api.get("/api/blog/")
    item = next(p for p in response.data["results"] if p["slug"] == published_post.slug)
    assert item["comments_count"] == 2


def test_creating_a_post_is_logged_in_the_activity_history(api, visitor, category):
    api.force_authenticate(user=visitor)
    api.post("/api/blog/", create_payload(category), format="multipart")

    assert ActivityLog.objects.filter(action="blog_post_submitted").exists()


@pytest.fixture
def published_post(admin, category):
    return BlogPost.objects.create(
        title="Post publicado",
        slug="post-publicado",
        summary="r",
        content="c",
        category=category,
        author=admin,
        status=BlogPost.Status.PUBLISHED,
        publication_date=timezone.now(),
    )


def test_authenticated_user_can_comment_on_a_post(api, visitor, published_post):
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/blog/{published_post.slug}/comments/", {"content": "¡Muy útil!"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["author_name"]

    comment = BlogComment.objects.get(post=published_post)
    assert comment.author == visitor
    assert comment.content == "¡Muy útil!"


def test_anonymous_cannot_comment(api, published_post):
    response = api.post(f"/api/blog/{published_post.slug}/comments/", {"content": "hola"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_comments_are_listed_for_a_post(api, visitor, published_post):
    BlogComment.objects.create(post=published_post, author=visitor, content="Primero")
    api.force_authenticate(user=visitor)
    response = api.get(f"/api/blog/{published_post.slug}/comments/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["content"] == "Primero"


# --- Activación programada (FeatureFlag "blog_module") ---------------------


@pytest.fixture
def blog_module_not_live():
    """Simula el estado "todavía no lanzado": sin fecha de activación."""
    FeatureFlag.objects.update_or_create(
        key="blog_module", defaults={"is_forced_active": False, "activate_at": None}
    )


def test_regular_user_sees_nothing_before_the_scheduled_launch(
    api, visitor, published_post, blog_module_not_live
):
    api.force_authenticate(user=visitor)
    response = api.get("/api/blog/")
    assert response.data["count"] == 0

    detail = api.get(f"/api/blog/{published_post.slug}/")
    assert detail.status_code == status.HTTP_404_NOT_FOUND

    comments = api.get(f"/api/blog/{published_post.slug}/comments/")
    assert comments.status_code == status.HTTP_404_NOT_FOUND


def test_staff_can_preview_before_the_scheduled_launch(
    api, admin, published_post, blog_module_not_live
):
    api.force_authenticate(user=admin)
    response = api.get("/api/blog/")
    assert response.data["count"] == 1

    comments = api.get(f"/api/blog/{published_post.slug}/comments/")
    assert comments.status_code == status.HTTP_200_OK


def test_regular_user_sees_it_once_the_scheduled_date_has_passed(
    api, visitor, published_post, blog_module_not_live
):
    FeatureFlag.objects.filter(key="blog_module").update(
        activate_at=timezone.now() - timezone.timedelta(minutes=1)
    )
    api.force_authenticate(user=visitor)
    response = api.get("/api/blog/")
    assert response.data["count"] == 1


def test_only_superadmin_can_edit_the_launch_date(api, admin, visitor):
    staff_not_super = User.objects.create_user(
        email="staff@example.com", password="ClaveSegura123", is_staff=True
    )

    api.force_authenticate(user=visitor)
    denied = api.patch("/api/feature-flags/blog_module/", {"activate_at": timezone.now()})
    assert denied.status_code == status.HTTP_403_FORBIDDEN

    api.force_authenticate(user=staff_not_super)
    denied_staff = api.patch("/api/feature-flags/blog_module/", {"activate_at": timezone.now()})
    assert denied_staff.status_code == status.HTTP_403_FORBIDDEN

    api.force_authenticate(user=admin)
    allowed = api.patch("/api/feature-flags/blog_module/", {"activate_at": timezone.now()})
    assert allowed.status_code == status.HTTP_200_OK
    assert allowed.data["is_active"] is True
