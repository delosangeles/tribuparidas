from datetime import date

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from apps.access.models import ModuleAccess
from apps.blog.models import BlogCategory, BlogComment, BlogPost
from apps.core.models import FeatureFlag
from apps.festejos.models import Festejo

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def modules_launched():
    """Como el resto de las pruebas, asumimos blog y festejos ya lanzados."""
    for key in ("blog_module", "festejos_module"):
        FeatureFlag.objects.update_or_create(key=key, defaults={"is_forced_active": True})


def make_user(email, **kwargs):
    kwargs.setdefault("is_active", True)
    return User.objects.create_user(email=email, password="x", **kwargs)


@pytest.fixture
def superadmin():
    return User.objects.create_superuser(email="super@example.com", password="x")


@pytest.fixture
def staff():
    return make_user("admin@example.com", is_staff=True)


@pytest.fixture
def madrina():
    return make_user("madrina@example.com", first_name="Madrina")


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def grant(user, module, categories=(), **actions):
    user.__dict__.pop("_module_access_cache", None)  # el caché es por petición; en tests el objeto se reutiliza
    access = ModuleAccess.objects.create(user=user, module=module, **{f"can_{k}": v for k, v in actions.items()})
    access.categories.set(BlogCategory.objects.filter(slug__in=categories))
    return access


def post_in(slug_category, status="IN_REVIEW", slug=None, author=None):
    category = BlogCategory.objects.get(slug=slug_category)
    author = author or make_user(f"autora-{slug or slug_category}@example.com")
    return BlogPost.objects.create(
        title=f"Post {slug_category}", slug=slug or f"post-{slug_category}", summary="r", content="c",
        category=category, author=author, status=status, publication_date=timezone.now(),
    )


# ---------- Gestión de madrinas (solo Super Admin) ----------

def test_only_super_admin_manages_madrinas(staff, madrina, superadmin):
    payload = {"access": [{"module": "blog", "can_approve": True}]}
    for user in (staff, madrina):
        assert client_for(user).get("/api/admin/madrinas/").status_code == 403
        assert client_for(user).put(f"/api/admin/madrinas/{madrina.id}/", payload, format="json").status_code == 403
    assert client_for(superadmin).put(f"/api/admin/madrinas/{madrina.id}/", payload, format="json").status_code == 200


def test_super_admin_assigns_blog_categories_and_removes(superadmin, madrina):
    lecturas = BlogCategory.objects.get(slug="lecturas")
    api = client_for(superadmin)
    res = api.put(
        f"/api/admin/madrinas/{madrina.id}/",
        {"access": [{"module": "blog", "can_approve": True, "can_delete": True, "categories": [lecturas.id]}]},
        format="json",
    )
    assert res.status_code == 200
    assert res.data["access"][0]["categories"][0]["slug"] == "lecturas"
    assert [m["id"] for m in api.get("/api/admin/madrinas/").data] == [madrina.id]

    assert api.delete(f"/api/admin/madrinas/{madrina.id}/").status_code == 204
    assert api.get("/api/admin/madrinas/").data == []


def test_cannot_assign_access_to_admins_or_without_actions(superadmin, staff, madrina):
    api = client_for(superadmin)
    ok = {"access": [{"module": "blog", "can_approve": True}]}
    assert api.put(f"/api/admin/madrinas/{staff.id}/", ok, format="json").status_code == 400
    assert api.put(f"/api/admin/madrinas/{madrina.id}/", {"access": [{"module": "blog"}]}, format="json").status_code == 400
    assert api.put(f"/api/admin/madrinas/{madrina.id}/", {"access": []}, format="json").status_code == 400
    # categorías solo aplican al blog
    bad = {"access": [{"module": "festejos", "can_add": True, "categories": [BlogCategory.objects.first().id]}]}
    assert api.put(f"/api/admin/madrinas/{madrina.id}/", bad, format="json").status_code == 400


def test_me_exposes_module_access_for_madrina_only(madrina, staff):
    grant(madrina, "blog", categories=["lecturas"], approve=True)
    data = client_for(madrina).get("/api/me/").data
    assert data["module_access"]["blog"]["approve"] is True
    assert data["module_access"]["blog"]["categories"] == ["lecturas"]
    assert client_for(staff).get("/api/me/").data["module_access"] is None


# ---------- Blog: acciones y alcance por categoría ----------

def test_madrina_approves_only_in_her_category(madrina):
    grant(madrina, "blog", categories=["lecturas"], approve=True)
    mine = post_in("lecturas")
    other = post_in("fit")
    api = client_for(madrina)

    assert api.post(f"/api/blog/{mine.slug}/approve/").status_code == 200
    mine.refresh_from_db()
    assert mine.status == "PUBLISHED"
    # el de otra categoría ni siquiera lo ve (está en revisión)
    assert api.post(f"/api/blog/{other.slug}/approve/").status_code in (403, 404)
    other.refresh_from_db()
    assert other.status == "IN_REVIEW"


def test_madrina_sees_in_review_only_in_her_category(madrina):
    grant(madrina, "blog", categories=["lecturas"], approve=True)
    post_in("lecturas", slug="mia")
    post_in("fit", slug="ajena")
    post_in("fit", status="PUBLISHED", slug="publicada-ajena")
    slugs = {p["slug"] for p in client_for(madrina).get("/api/blog/").data["results"]}
    assert slugs == {"mia", "publicada-ajena"}


def test_madrina_without_category_limit_manages_all_categories(madrina):
    grant(madrina, "blog", approve=True)
    assert client_for(madrina).post(f"/api/blog/{post_in('fit').slug}/approve/").status_code == 200


def test_madrina_needs_the_specific_action(madrina):
    grant(madrina, "blog", categories=["lecturas"], approve=True)  # solo aprobar
    post = post_in("lecturas", status="PUBLISHED")
    api = client_for(madrina)
    assert api.patch(f"/api/blog/{post.slug}/", {"title": "nuevo"}, format="json").status_code == 403
    assert api.delete(f"/api/blog/{post.slug}/").status_code == 403


def test_madrina_edits_and_deletes_only_inside_scope(madrina):
    grant(madrina, "blog", categories=["lecturas"], edit=True, delete=True)
    mine = post_in("lecturas", status="PUBLISHED", slug="mia")
    other = post_in("fit", status="PUBLISHED", slug="ajena")
    api = client_for(madrina)

    assert api.patch(f"/api/blog/{mine.slug}/", {"title": "Editado"}, format="json").status_code == 200
    assert api.patch(f"/api/blog/{other.slug}/", {"title": "x"}, format="json").status_code == 403
    assert api.delete(f"/api/blog/{other.slug}/").status_code == 403
    assert api.delete(f"/api/blog/{mine.slug}/").status_code == 204
    # no puede mover su post a una categoría que no administra
    again = post_in("lecturas", status="PUBLISHED", slug="otra-mia")
    fit = BlogCategory.objects.get(slug="fit")
    assert api.patch(f"/api/blog/{again.slug}/", {"category": fit.id}, format="json").status_code == 403


def test_madrina_with_add_publishes_directly_in_her_category(madrina):
    grant(madrina, "blog", categories=["lecturas"], add=True)
    lecturas = BlogCategory.objects.get(slug="lecturas")
    fit = BlogCategory.objects.get(slug="fit")
    api = client_for(madrina)
    def body(title, category):
        return {
            "title": title, "slug": title.lower().replace(" ", "-"), "summary": "r", "content": "c",
            "category": category.id, "status": "PUBLISHED", "visibility": "public", "reading_time": 3,
        }

    res = api.post("/api/blog/", body("Mi lectura", lecturas), format="multipart")
    assert res.status_code == 201, res.data
    assert BlogPost.objects.get(slug="mi-lectura").status == "PUBLISHED"
    # fuera de su alcance se comporta como cualquier usuaria: queda en revisión
    res = api.post("/api/blog/", body("En fit", fit), format="multipart")
    assert res.status_code == 201, res.data
    assert BlogPost.objects.get(slug="en-fit").status == "IN_REVIEW"


def test_madrina_deletes_comments_only_in_her_category(madrina):
    grant(madrina, "blog", categories=["lecturas"], delete=True)
    mine = post_in("lecturas", status="PUBLISHED", slug="mia")
    other = post_in("fit", status="PUBLISHED", slug="ajena")
    commenter = make_user("comenta@example.com")
    c_mine = BlogComment.objects.create(post=mine, author=commenter, content="hola")
    c_other = BlogComment.objects.create(post=other, author=commenter, content="hola")
    api = client_for(madrina)

    listed = api.get(f"/api/blog/{mine.slug}/comments/").data["results"]
    assert listed[0]["can_delete"] is True
    assert api.get(f"/api/blog/{other.slug}/comments/").data["results"][0]["can_delete"] is False

    assert api.delete(f"/api/blog/{other.slug}/comments/{c_other.id}/").status_code == 403
    assert api.delete(f"/api/blog/{mine.slug}/comments/{c_mine.id}/").status_code == 204


def test_regular_user_has_no_moderation_rights():
    user = make_user("normal@example.com")
    post = post_in("lecturas", status="PUBLISHED")
    commenter = make_user("c@example.com")
    comment = BlogComment.objects.create(post=post, author=commenter, content="x")
    api = client_for(user)
    assert api.post(f"/api/blog/{post.slug}/approve/").status_code == 403
    assert api.delete(f"/api/blog/{post.slug}/").status_code == 403
    assert api.delete(f"/api/blog/{post.slug}/comments/{comment.id}/").status_code == 403


# ---------- Festejos ----------

def test_madrina_festejos_actions_follow_assigned_permissions(madrina):
    owner = make_user("mama@example.com", birth_date=date(1990, 1, 1))
    festejo = Festejo.objects.create(kind="manual", event_date=date(2026, 10, 10), user=owner, title="x")
    api = client_for(madrina)

    # sin acceso al módulo no puede nada
    assert api.post(f"/api/festejos/{festejo.id}/approve/").status_code == 403

    grant(madrina, "festejos", approve=True)
    assert api.post(f"/api/festejos/{festejo.id}/approve/").status_code == 200
    body = {"kind": "manual", "event_date": "2026-10-11", "user": owner.id, "title": "nuevo"}
    assert api.post("/api/festejos/", body, format="json").status_code == 403  # sin "agregar"
    assert api.delete(f"/api/festejos/{festejo.id}/").status_code == 403  # sin "eliminar"


def test_madrina_with_festejos_access_sees_pending(madrina):
    owner = make_user("mama@example.com")
    Festejo.objects.create(kind="manual", event_date=date(2026, 10, 10), user=owner, title="pendiente")
    grant(madrina, "festejos", approve=True)
    res = client_for(madrina).get("/api/festejos/?scope=month&date=2026-10-10")
    assert [f["title"] for f in res.data["results"]] == ["pendiente"]


# ---------- Usuarios ----------

def test_madrina_users_approve_vs_edit(madrina):
    waiting = make_user("espera@example.com", is_active=False, first_name="Ana")
    api = client_for(madrina)
    assert api.get("/api/admin/users/").status_code == 403  # sin acceso al módulo

    grant(madrina, "usuarios", approve=True)
    assert api.get("/api/admin/users/").status_code == 200
    assert api.get("/api/admin/users/summary/").status_code == 200
    assert api.patch(f"/api/admin/users/{waiting.id}/", {"is_active": True}, format="json").status_code == 200
    assert api.patch(f"/api/admin/users/{waiting.id}/", {"first_name": "Otro"}, format="json").status_code == 403
    assert api.post(f"/api/admin/users/{waiting.id}/reset_password/").status_code == 403


def test_madrina_cannot_touch_admin_accounts_or_roles(madrina, staff, superadmin):
    grant(madrina, "usuarios", edit=True, approve=True)
    api = client_for(madrina)
    assert api.patch(f"/api/admin/users/{staff.id}/", {"is_active": False}, format="json").status_code == 403
    assert api.patch(f"/api/admin/users/{superadmin.id}/", {"first_name": "x"}, format="json").status_code == 403
    assert api.post(f"/api/admin/users/{madrina.id}/set_role/", {"is_staff": True}, format="json").status_code == 403
    assert api.post("/api/admin/users/", {"email": "n@example.com"}, format="json").status_code == 403


def test_madrina_cannot_reach_other_admin_modules(madrina):
    grant(madrina, "blog", approve=True)
    api = client_for(madrina)
    assert api.get("/api/admin/users/").status_code == 403
    assert api.get("/api/admin/notifications/").status_code == 403
    assert api.get("/api/admin/madrinas/").status_code == 403
    assert api.get("/api/admin/reports/monthly/").status_code == 403
