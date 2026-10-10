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
        "visibility": "public",
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


def test_anonymous_can_read_blog_and_comments_but_not_write(api, published_post):
    assert api.get("/api/blog/").data["count"] == 1
    assert api.get(f"/api/blog/{published_post.slug}/").status_code == status.HTTP_200_OK
    assert api.get(f"/api/blog/{published_post.slug}/comments/").status_code == status.HTTP_200_OK
    assert api.get("/api/blog/categories/").status_code == status.HTTP_200_OK
    assert api.post("/api/blog/", {"title": "x"}).status_code == status.HTTP_401_UNAUTHORIZED


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


def test_comment_exposes_author_photo_publicly(api, visitor, published_post):
    visitor.photo = "users/photos/yo.png"
    visitor.save()
    BlogComment.objects.create(post=published_post, author=visitor, content="Hola")
    results = api.get(f"/api/blog/{published_post.slug}/comments/").data["results"]
    assert results[0]["author_photo"].endswith("users/photos/yo.png")


def test_comment_author_photo_is_null_without_picture(api, visitor, published_post):
    BlogComment.objects.create(post=published_post, author=visitor, content="Hola")
    assert api.get(f"/api/blog/{published_post.slug}/comments/").data["results"][0]["author_photo"] is None


def test_created_comment_returns_absolute_author_photo(api, visitor, published_post):
    visitor.photo = "users/photos/yo.png"
    visitor.save()
    api.force_authenticate(user=visitor)
    response = api.post(f"/api/blog/{published_post.slug}/comments/", {"content": "Hola"})
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["author_photo"].startswith("http")


# --- Respuestas, reacciones, fotos, edición y moderación de comentarios ------

import io  # noqa: E402

from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from PIL import Image  # noqa: E402


@pytest.fixture
def media(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    return tmp_path


def comment_png(name="foto.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (6, 6), "pink").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@pytest.fixture
def other_user(db):
    return User.objects.create_user(email="otra@example.com", password="ClaveSegura123", first_name="Otra")


def comments_url(post):
    return f"/api/blog/{post.slug}/comments/"


def test_reply_is_nested_under_the_parent_comment(api, visitor, other_user, published_post):
    parent = BlogComment.objects.create(post=published_post, author=other_user, content="Principal")
    api.force_authenticate(user=visitor)
    response = api.post(comments_url(published_post), {"content": "Respuesta", "parent": parent.pk}, format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["parent"] == parent.pk

    listing = api.get(comments_url(published_post)).data["results"]
    assert [c["id"] for c in listing] == [parent.pk]  # solo los principales
    assert [r["content"] for r in listing[0]["replies"]] == ["Respuesta"]


def test_reply_to_a_reply_is_attached_to_the_root_comment(api, visitor, other_user, published_post):
    root = BlogComment.objects.create(post=published_post, author=other_user, content="Raíz")
    reply = BlogComment.objects.create(post=published_post, author=other_user, content="Hija", parent=root)
    api.force_authenticate(user=visitor)
    response = api.post(comments_url(published_post), {"content": "Nieta", "parent": reply.pk}, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["parent"] == root.pk


def test_cannot_reply_to_a_comment_of_another_post(api, visitor, other_user, published_post, category):
    other_post = BlogPost.objects.create(
        title="Otro", slug="otro", summary="x", content="x", category=category, status=BlogPost.Status.PUBLISHED,
        publication_date=published_post.publication_date, author=other_user,
    )
    foreign = BlogComment.objects.create(post=other_post, author=other_user, content="Ajeno")
    api.force_authenticate(user=visitor)
    response = api.post(comments_url(published_post), {"content": "x", "parent": foreign.pk}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_comment_with_only_a_photo_is_allowed_and_empty_is_not(api, visitor, published_post, media):
    api.force_authenticate(user=visitor)
    empty = api.post(comments_url(published_post), {"content": "  "}, format="json")
    assert empty.status_code == status.HTTP_400_BAD_REQUEST

    with_photo = api.post(comments_url(published_post), {"image": comment_png()}, format="multipart")
    assert with_photo.status_code == status.HTTP_201_CREATED, with_photo.data
    assert with_photo.data["image"].startswith("http")
    stored = BlogComment.objects.get(pk=with_photo.data["id"])
    assert stored.image.name.startswith("blog/comments/") and "foto" not in stored.image.name


def test_comment_photo_must_be_an_image(api, visitor, published_post, media):
    api.force_authenticate(user=visitor)
    fake = SimpleUploadedFile("x.png", b"no soy imagen", content_type="image/png")
    response = api.post(comments_url(published_post), {"content": "hola", "image": fake}, format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_like_toggles_and_counts(api, visitor, other_user, published_post):
    comment = BlogComment.objects.create(post=published_post, author=other_user, content="Hola")
    url = f"{comments_url(published_post)}{comment.pk}/like/"
    api.force_authenticate(user=visitor)

    first = api.post(url)
    assert first.data == {"liked": True, "like_count": 1}
    listing = api.get(comments_url(published_post)).data["results"][0]
    assert listing["like_count"] == 1 and listing["liked_by_me"] is True

    second = api.post(url)
    assert second.data == {"liked": False, "like_count": 0}


def test_like_requires_login_and_anonymous_sees_counts(api, visitor, other_user, published_post):
    comment = BlogComment.objects.create(post=published_post, author=other_user, content="Hola")
    url = f"{comments_url(published_post)}{comment.pk}/like/"
    assert api.post(url).status_code == status.HTTP_401_UNAUTHORIZED

    api.force_authenticate(user=visitor)
    api.post(url)
    api.force_authenticate(user=None)
    listing = api.get(comments_url(published_post)).data["results"][0]
    assert listing["like_count"] == 1 and listing["liked_by_me"] is False


def test_author_can_edit_own_comment_and_it_is_marked_edited(api, visitor, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Antes")
    api.force_authenticate(user=visitor)
    response = api.patch(f"{comments_url(published_post)}{comment.pk}/", {"content": "Después"}, format="json")
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["content"] == "Después"
    assert response.data["edited_at"] is not None


def test_author_can_replace_and_remove_the_photo(api, visitor, published_post, media):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Con foto", image="blog/comments/vieja.png")
    url = f"{comments_url(published_post)}{comment.pk}/"
    api.force_authenticate(user=visitor)

    replaced = api.patch(url, {"image": comment_png("nueva.png")}, format="multipart")
    assert replaced.status_code == status.HTTP_200_OK, replaced.data
    comment.refresh_from_db()
    assert comment.image.name.startswith("blog/comments/") and comment.image.name != "blog/comments/vieja.png"

    removed = api.patch(url, {"remove_image": True}, format="json")
    assert removed.data["image"] is None
    comment.refresh_from_db()
    assert not comment.image


def test_cannot_empty_a_comment_by_editing(api, visitor, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Algo")
    api.force_authenticate(user=visitor)
    response = api.patch(f"{comments_url(published_post)}{comment.pk}/", {"content": ""}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_nobody_else_can_edit_a_comment_not_even_an_admin(api, visitor, other_user, admin, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Mío")
    url = f"{comments_url(published_post)}{comment.pk}/"
    for user in (other_user, admin):
        api.force_authenticate(user=user)
        assert api.patch(url, {"content": "hackeado"}, format="json").status_code == status.HTTP_403_FORBIDDEN
    comment.refresh_from_db()
    assert comment.content == "Mío"


def test_anonymous_cannot_edit_or_delete(api, visitor, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Mío")
    url = f"{comments_url(published_post)}{comment.pk}/"
    assert api.patch(url, {"content": "x"}, format="json").status_code == status.HTTP_401_UNAUTHORIZED
    assert api.delete(url).status_code == status.HTTP_401_UNAUTHORIZED


def test_author_can_delete_own_comment_with_its_replies(api, visitor, other_user, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Mío")
    BlogComment.objects.create(post=published_post, author=other_user, content="Respuesta", parent=comment)
    api.force_authenticate(user=visitor)
    assert api.delete(f"{comments_url(published_post)}{comment.pk}/").status_code == status.HTTP_204_NO_CONTENT
    assert BlogComment.objects.count() == 0


def test_other_user_cannot_delete_someone_elses_comment(api, visitor, other_user, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Mío")
    api.force_authenticate(user=other_user)
    assert api.delete(f"{comments_url(published_post)}{comment.pk}/").status_code == status.HTTP_403_FORBIDDEN
    assert BlogComment.objects.filter(pk=comment.pk).exists()


def test_admin_can_delete_any_comment_and_it_is_logged(api, visitor, admin, published_post):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Inapropiado")
    api.force_authenticate(user=admin)
    assert api.delete(f"{comments_url(published_post)}{comment.pk}/").status_code == status.HTTP_204_NO_CONTENT
    assert not BlogComment.objects.filter(pk=comment.pk).exists()
    assert ActivityLog.objects.filter(action="blog_comment_deleted", actor=admin).exists()


def test_comment_detail_is_hidden_before_the_blog_launch(api, visitor, published_post, blog_module_not_live):
    comment = BlogComment.objects.create(post=published_post, author=visitor, content="Mío")
    api.force_authenticate(user=visitor)
    assert api.patch(f"{comments_url(published_post)}{comment.pk}/", {"content": "x"}, format="json").status_code == status.HTTP_404_NOT_FOUND


# --- Categoría "Desahogos": única que se publica sin aprobación ---------------


@pytest.fixture
def desahogos(db):
    return BlogCategory.objects.get_or_create(slug="desahogos", defaults={"name": "Desahogos"})[0]


def post_payload(category, **extra):
    return {"title": "Lo que llevo dentro", "slug": "lo-que-llevo-dentro", "visibility": "public", "summary": "Un resumen", "content": "Hoy necesito soltar esto.", "category": category.pk, **extra}


def test_desahogos_category_is_seeded_by_migration(db):
    assert BlogCategory.objects.filter(slug="desahogos", name="Desahogos", is_active=True).exists()


def test_member_publishes_in_desahogos_without_approval(api, visitor, desahogos):
    api.force_authenticate(user=visitor)
    response = api.post("/api/blog/", post_payload(desahogos), format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["status"] == BlogPost.Status.PUBLISHED
    post = BlogPost.objects.get(slug=response.data["slug"])
    assert post.status == BlogPost.Status.PUBLISHED
    assert post.author == visitor
    assert post.publication_date is not None
    assert ActivityLog.objects.filter(action="blog_post_published_open", actor=visitor).exists()

    # y ya lo ve cualquiera, sin sesión
    api.force_authenticate(user=None)
    assert [p["title"] for p in api.get("/api/blog/").data["results"]] == ["Lo que llevo dentro"]


def test_member_post_in_any_other_category_still_needs_approval(api, visitor, category):
    api.force_authenticate(user=visitor)
    response = api.post("/api/blog/", post_payload(category), format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["status"] == BlogPost.Status.IN_REVIEW
    api.force_authenticate(user=None)
    assert api.get("/api/blog/").data["count"] == 0


def test_member_cannot_force_status_or_feature_in_desahogos(api, visitor, desahogos):
    api.force_authenticate(user=visitor)
    response = api.post(
        "/api/blog/",
        post_payload(desahogos, status=BlogPost.Status.DRAFT, featured=True, publication_date="2030-01-01T00:00:00Z"),
        format="json",
    )
    post = BlogPost.objects.get(slug=response.data["slug"])
    assert post.status == BlogPost.Status.PUBLISHED  # lo decide el servidor, no el cliente
    assert post.featured is False
    assert post.publication_date <= timezone.now()


def test_anonymous_cannot_publish_in_desahogos(api, desahogos):
    assert api.post("/api/blog/", post_payload(desahogos), format="json").status_code == status.HTTP_401_UNAUTHORIZED


def test_desahogos_is_hidden_before_the_blog_launch_for_members(api, visitor, desahogos, blog_module_not_live):
    api.force_authenticate(user=visitor)
    api.post("/api/blog/", post_payload(desahogos), format="json")
    assert api.get("/api/blog/").data["count"] == 0


# --- Visibilidad de los blogs: público (cualquiera) / privado (con sesión) ----


def make_post(admin, category, visibility, slug):
    return BlogPost.objects.create(
        title=f"Blog {visibility}", slug=slug, summary="x", content="x", category=category,
        status=BlogPost.Status.PUBLISHED, publication_date=timezone.now() - timezone.timedelta(days=1),
        author=admin, visibility=visibility,
    )


def test_existing_style_posts_default_to_public(admin, category):
    post = BlogPost.objects.create(title="Viejo", slug="viejo", summary="x", content="x", category=category, author=admin)
    assert post.visibility == BlogPost.Visibility.PUBLIC


def test_anonymous_only_sees_public_blogs(api, admin, category):
    make_post(admin, category, "public", "abierto")
    make_post(admin, category, "private", "cerrado")
    assert [p["slug"] for p in api.get("/api/blog/").data["results"]] == ["abierto"]
    assert api.get("/api/blog/abierto/").status_code == status.HTTP_200_OK
    assert api.get("/api/blog/cerrado/").status_code == status.HTTP_404_NOT_FOUND


def test_logged_in_user_sees_public_and_private_blogs(api, visitor, admin, category):
    make_post(admin, category, "public", "abierto")
    make_post(admin, category, "private", "cerrado")
    api.force_authenticate(user=visitor)
    assert {p["slug"] for p in api.get("/api/blog/").data["results"]} == {"abierto", "cerrado"}
    detail = api.get("/api/blog/cerrado/")
    assert detail.status_code == status.HTTP_200_OK and detail.data["visibility"] == "private"


def test_comments_of_a_private_blog_need_login_to_read(api, visitor, admin, category):
    post = make_post(admin, category, "private", "cerrado")
    BlogComment.objects.create(post=post, author=admin, content="Solo tribu")
    assert api.get("/api/blog/cerrado/comments/").status_code == status.HTTP_404_NOT_FOUND
    api.force_authenticate(user=visitor)
    assert api.get("/api/blog/cerrado/comments/").status_code == status.HTTP_200_OK


def test_visibility_is_required_when_creating_a_blog(api, admin, category):
    api.force_authenticate(user=admin)
    payload = create_payload(category)
    payload.pop("visibility")
    response = api.post("/api/blog/", payload, format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "visibility" in response.data


def test_visibility_rejects_unknown_values(api, admin, category):
    api.force_authenticate(user=admin)
    response = api.post("/api/blog/", create_payload(category, visibility="secreto"), format="multipart")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_member_choice_of_private_is_kept_even_when_published_in_desahogos(api, visitor, desahogos):
    api.force_authenticate(user=visitor)
    response = api.post("/api/blog/", post_payload(desahogos, visibility="private"), format="json")
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["status"] == BlogPost.Status.PUBLISHED
    assert response.data["visibility"] == "private"
    api.force_authenticate(user=None)
    assert api.get("/api/blog/").data["count"] == 0  # publicado, pero solo con sesión


def test_admin_can_change_visibility_when_editing(api, admin, category):
    post = make_post(admin, category, "public", "cambiar")
    api.force_authenticate(user=admin)
    response = api.patch(f"/api/blog/{post.slug}/", {"visibility": "private"}, format="json")
    assert response.status_code == status.HTTP_200_OK, response.data
    post.refresh_from_db()
    assert post.visibility == BlogPost.Visibility.PRIVATE
