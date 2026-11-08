import io

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.access.models import ModuleAccess
from apps.core.models import ActivityLog, FeatureFlag

from .models import AgeRange, Allergen, FavoriteRecipe, FoodItem, GuideArticle, MealType, Recipe, SafetyContent, Status
from .text import normalize_text

User = get_user_model()
BASE = "/api/alimentacion"


@pytest.fixture(autouse=True)
def activate_module(db, settings, tmp_path):
    """Los tests asumen el módulo ya lanzado; el gate tiene sus propios tests."""
    FeatureFlag.objects.update_or_create(key="alimentacion_module", defaults={"is_forced_active": True})
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def not_live(db):
    FeatureFlag.objects.update_or_create(key="alimentacion_module", defaults={"is_forced_active": False, "activate_at": None})


def client(user=None):
    api = APIClient()
    if user:
        api.force_authenticate(user=user)
    return api


def jwt_client(user):
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return api


@pytest.fixture
def user(db):
    return User.objects.create_user(email="mama@example.com", password="x")


@pytest.fixture
def admin(db):
    return User.objects.create_user(email="admin@example.com", password="x", is_staff=True)


@pytest.fixture
def madrina(db):
    u = User.objects.create_user(email="madrina@example.com", password="x")
    ModuleAccess.objects.create(user=u, module="alimentacion", can_add=True, can_edit=True)
    return u


@pytest.fixture
def cats(db):
    return {
        "age": AgeRange.objects.get(slug="6-8-meses"),
        "age2": AgeRange.objects.get(slug="9-11-meses"),
        "meal": MealType.objects.get(slug="pure"),
        "meal2": MealType.objects.get(slug="snack"),
        "egg": Allergen.objects.create(name="Huevo"),
        "nut": Allergen.objects.create(name="Maní"),
    }


def make_recipe(cats, title="Puré de zanahoria", status=Status.PUBLISHED, **kw):
    recipe = Recipe.objects.create(
        title=title, age_range=kw.pop("age", cats["age"]), meal_type=kw.pop("meal", cats["meal"]), status=status
    )
    recipe.allergens.set(kw.pop("allergens", []))
    return recipe


def png(name="a.png", size=(10, 10)):
    buf = io.BytesIO()
    Image.new("RGB", size, "white").save(buf, "PNG")
    return SimpleUploadedFile(name, buf.getvalue(), content_type="image/png")


def recipe_payload(cats, **extra):
    return {
        "title": "Receta nueva",
        "age_range": cats["age"].id,
        "meal_type": cats["meal"].id,
        "allergens": [cats["egg"].id],
        "ingredients": [{"name": "Zanahoria", "quantity": ""}, {"name": "Agua", "quantity": ""}],
        "steps": [{"text": "Paso uno"}, {"text": "Paso dos"}],
        **extra,
    }


# ---------- Utilidades ----------

def test_normalize_text_removes_accents_and_case():
    assert normalize_text("  Puré De MANÍ ") == "pure de mani"


def test_catalogs_are_seeded_and_allergens_are_not(db):
    assert list(AgeRange.objects.values_list("slug", flat=True)) == ["6-8-meses", "9-11-meses", "12-meses"]
    assert MealType.objects.count() == 5
    assert Allergen.objects.count() == 0


def test_slug_is_unique_and_generated(cats):
    a = make_recipe(cats, "Mi receta")
    b = make_recipe(cats, "Mi receta")
    assert a.slug == "mi-receta" and b.slug == "mi-receta-2"


# ---------- Flag apagado / encendido ----------

def test_flag_off_public_api_returns_404_for_visitors_and_users(cats, user, not_live):
    make_recipe(cats)
    for who in (client(), client(user)):
        for path in ("/recetas/", "/guias/", "/alimentos/", "/seguridad/", "/catalogos/"):
            assert who.get(BASE + path).status_code == 404, path
    assert client(user).get(BASE + "/favoritos/").status_code == 404


def test_flag_off_staff_and_madrina_still_see_it(cats, admin, madrina, not_live):
    make_recipe(cats)
    assert len(client(admin).get(BASE + "/recetas/").data) == 1
    assert client(madrina).get(BASE + "/recetas/").status_code == 200


def test_flag_on_visitors_read_published_only(cats):
    make_recipe(cats, "Publicada")
    make_recipe(cats, "Borrador", status=Status.DRAFT)
    data = client().get(BASE + "/recetas/").data
    assert [r["title"] for r in data] == ["Publicada"]


def test_missing_flag_behaves_as_live(cats):
    FeatureFlag.objects.filter(key="alimentacion_module").delete()
    assert client().get(BASE + "/recetas/").status_code == 200


def test_flag_scheduled_in_future_is_off(cats):
    from datetime import timedelta
    from django.utils import timezone

    FeatureFlag.objects.update_or_create(
        key="alimentacion_module",
        defaults={"is_forced_active": False, "activate_at": timezone.now() + timedelta(days=1)},
    )
    assert client().get(BASE + "/recetas/").status_code == 404


# ---------- Borradores y vista previa ----------

def test_draft_detail_hidden_but_preview_for_team(cats, admin, user):
    r = make_recipe(cats, "Secreta", status=Status.DRAFT)
    assert client().get(f"{BASE}/recetas/{r.slug}/").status_code == 404
    assert client(user).get(f"{BASE}/recetas/{r.slug}/?preview=1").status_code == 404
    assert client(admin).get(f"{BASE}/recetas/{r.slug}/?preview=1").status_code == 200
    assert client(admin).get(f"{BASE}/recetas/{r.slug}/").status_code == 404


def test_safety_hidden_until_published(admin):
    assert client().get(BASE + "/seguridad/").data == {"published": False}
    obj = SafetyContent.get_solo()
    obj.content, obj.professional_name, obj.status = "<p>x</p>", "Dra. Ejemplo", Status.PUBLISHED
    obj.save()
    data = client().get(BASE + "/seguridad/").data
    assert data["published"] and data["professional_name"] == "Dra. Ejemplo"


# ---------- Búsqueda y filtros ----------

def test_search_ignores_accents_and_matches_ingredients(cats, admin):
    r = make_recipe(cats, "Crema de manzana")
    r.ingredients.create(name="Plátano")
    r.refresh_search_text()
    make_recipe(cats, "Otra cosa")
    api = client()
    assert [x["slug"] for x in api.get(BASE + "/recetas/", {"q": "MANZANA"}).data] == [r.slug]
    assert len(api.get(BASE + "/recetas/", {"q": "platano"}).data) == 1
    assert len(api.get(BASE + "/recetas/", {"q": "plátano"}).data) == 1
    assert api.get(BASE + "/recetas/", {"q": "inexistente"}).data == []


def test_filters_by_age_type_and_without_allergen(cats):
    a = make_recipe(cats, "A", age=cats["age"], meal=cats["meal"], allergens=[cats["egg"]])
    b = make_recipe(cats, "B", age=cats["age2"], meal=cats["meal2"])
    c = make_recipe(cats, "C", age=cats["age"], meal=cats["meal"], allergens=[cats["nut"]])
    api = client()
    slugs = lambda params: sorted(r["slug"] for r in api.get(BASE + "/recetas/", params).data)  # noqa: E731
    assert slugs({"edad": "6-8-meses"}) == sorted([a.slug, c.slug])
    assert slugs({"tipo": "snack"}) == [b.slug]
    assert slugs({"sin_alergeno": "huevo"}) == sorted([b.slug, c.slug])
    assert slugs({"sin_alergeno": "huevo,mani"}) == [b.slug]
    assert slugs({"edad": "6-8-meses", "sin_alergeno": "huevo"}) == [c.slug]


def test_recipe_detail_has_ingredients_steps_and_allergens(cats):
    r = make_recipe(cats, allergens=[cats["egg"]])
    r.ingredients.create(name="Zanahoria", order=0)
    r.steps.create(text="Cocer", order=0)
    data = client().get(f"{BASE}/recetas/{r.slug}/").data
    assert data["ingredients"][0]["name"] == "Zanahoria"
    assert data["steps"][0]["text"] == "Cocer"
    assert data["allergens"][0]["name"] == "Huevo"


def test_catalogs_endpoint_lists_only_active(cats):
    cats["egg"].is_active = False
    cats["egg"].save()
    names = [a["name"] for a in client().get(BASE + "/catalogos/").data["allergens"]]
    assert names == ["Maní"]


# ---------- Favoritos ----------

def test_favorites_require_login(cats):
    r = make_recipe(cats)
    assert client().post(f"{BASE}/recetas/{r.slug}/favorito/").status_code == 401
    assert client().get(BASE + "/favoritos/").status_code == 401


def test_favorite_add_list_remove_and_no_duplicates(cats, user):
    r = make_recipe(cats)
    api = client(user)
    assert api.post(f"{BASE}/recetas/{r.slug}/favorito/").status_code == 201
    api.post(f"{BASE}/recetas/{r.slug}/favorito/")
    assert FavoriteRecipe.objects.filter(user=user).count() == 1
    assert [x["slug"] for x in api.get(BASE + "/favoritos/").data] == [r.slug]
    assert api.get(BASE + "/recetas/").data[0]["is_favorite"] is True
    assert client().get(BASE + "/recetas/").data[0]["is_favorite"] is False
    assert api.delete(f"{BASE}/recetas/{r.slug}/favorito/").status_code == 204
    assert api.get(BASE + "/favoritos/").data == []


def test_favorites_are_private_per_user(cats, user):
    other = User.objects.create_user(email="otra@example.com", password="x")
    r = make_recipe(cats)
    client(user).post(f"{BASE}/recetas/{r.slug}/favorito/")
    assert client(other).get(BASE + "/favoritos/").data == []


def test_cannot_favorite_a_draft(cats, user):
    r = make_recipe(cats, status=Status.DRAFT)
    assert client(user).post(f"{BASE}/recetas/{r.slug}/favorito/").status_code == 404


def test_unpublished_favorite_disappears_from_list(cats, user):
    r = make_recipe(cats)
    client(user).post(f"{BASE}/recetas/{r.slug}/favorito/")
    r.status = Status.DRAFT
    r.save()
    assert client(user).get(BASE + "/favoritos/").data == []


def test_unapproved_and_portal_accounts_cannot_use_favorites(cats):
    r = make_recipe(cats)
    unapproved = User.objects.create_user(email="u@example.com", password="x", is_approved=False)
    portal = User.objects.create_user(email="p@example.com", password="x", account_type="portal")
    for account in (unapproved, portal):
        api = jwt_client(account)
        assert api.post(f"{BASE}/recetas/{r.slug}/favorito/").status_code == 403
        assert api.get(BASE + "/favoritos/").status_code == 401  # lectura: se trata como visitante
        assert api.get(BASE + "/recetas/").status_code == 200  # lo público sí lo lee


# ---------- Permisos de escritura ----------

ADMIN_PATHS = ["/admin/recetas/", "/admin/guias/", "/admin/alimentos/", "/admin/edades/", "/admin/alergenos/", "/admin/tipos/"]


def test_admin_endpoints_reject_visitors_and_regular_users(cats, user):
    for path in ADMIN_PATHS:
        assert client().get(BASE + path).status_code in (401, 403), path
        assert client(user).get(BASE + path).status_code == 403, path
        assert client(user).post(BASE + path, {}, format="json").status_code == 403, path
    assert client(user).patch(BASE + "/admin/seguridad/", {"content": "x"}, format="json").status_code == 403
    assert client().get(BASE + "/admin/seguridad/").status_code == 401


def test_admin_can_create_recipe_with_children_and_it_is_logged(cats, admin):
    response = client(admin).post(BASE + "/admin/recetas/", recipe_payload(cats, status="published"), format="json")
    assert response.status_code == 201, response.data
    recipe = Recipe.objects.get(pk=response.data["id"])
    assert [i.name for i in recipe.ingredients.all()] == ["Zanahoria", "Agua"]
    assert [s.text for s in recipe.steps.all()] == ["Paso uno", "Paso dos"]
    assert list(recipe.allergens.all()) == [cats["egg"]]
    assert "zanahoria" in recipe.search_text
    assert ActivityLog.objects.filter(action="alimentacion_recipe_created", actor=admin).exists()


def test_update_replaces_children_and_delete_is_logged(cats, admin):
    api = client(admin)
    rid = api.post(BASE + "/admin/recetas/", recipe_payload(cats), format="json").data["id"]
    response = api.patch(
        f"{BASE}/admin/recetas/{rid}/",
        {"ingredients": [{"name": "Pera", "quantity": ""}], "title": "Cambiada"},
        format="json",
    )
    assert response.status_code == 200
    recipe = Recipe.objects.get(pk=rid)
    assert [i.name for i in recipe.ingredients.all()] == ["Pera"]
    assert recipe.steps.count() == 2  # no enviados: se conservan
    assert ActivityLog.objects.filter(action="alimentacion_recipe_updated").exists()
    assert api.delete(f"{BASE}/admin/recetas/{rid}/").status_code == 204
    assert ActivityLog.objects.filter(action="alimentacion_recipe_deleted").exists()


def test_madrina_can_draft_but_not_publish_or_delete(cats, madrina):
    api = client(madrina)
    created = api.post(BASE + "/admin/recetas/", recipe_payload(cats), format="json")
    assert created.status_code == 201 and created.data["status"] == "draft"
    rid = created.data["id"]
    assert api.post(BASE + "/admin/recetas/", recipe_payload(cats, status="published"), format="json").status_code == 403
    assert api.patch(f"{BASE}/admin/recetas/{rid}/", {"status": "published"}, format="json").status_code == 403
    assert api.post(f"{BASE}/admin/recetas/{rid}/publish/").status_code == 403
    assert api.delete(f"{BASE}/admin/recetas/{rid}/").status_code == 403
    assert Recipe.objects.get(pk=rid).status == "draft"


def test_madrina_with_approve_can_publish_and_unpublish(cats):
    u = User.objects.create_user(email="m2@example.com", password="x")
    ModuleAccess.objects.create(user=u, module="alimentacion", can_add=True, can_edit=True, can_approve=True)
    r = make_recipe(cats, status=Status.DRAFT)
    api = client(u)
    assert api.post(f"{BASE}/admin/recetas/{r.id}/publish/").data["status"] == "published"
    assert api.post(f"{BASE}/admin/recetas/{r.id}/unpublish/").data["status"] == "draft"
    assert ActivityLog.objects.filter(action="alimentacion_recipe_published").exists()
    assert ActivityLog.objects.filter(action="alimentacion_recipe_unpublished").exists()


def test_madrina_of_other_module_has_no_access(cats):
    u = User.objects.create_user(email="blog@example.com", password="x")
    ModuleAccess.objects.create(user=u, module="blog", can_add=True, can_edit=True)
    assert client(u).get(BASE + "/admin/recetas/").status_code == 403


def test_readonly_madrina_cannot_write(cats):
    u = User.objects.create_user(email="ro@example.com", password="x")
    ModuleAccess.objects.create(user=u, module="alimentacion")
    assert client(u).get(BASE + "/admin/recetas/").status_code == 200
    assert client(u).post(BASE + "/admin/recetas/", recipe_payload(cats), format="json").status_code == 403


def test_admin_list_includes_drafts_and_filters_by_status(cats, admin):
    make_recipe(cats, "P")
    make_recipe(cats, "D", status=Status.DRAFT)
    api = client(admin)
    assert len(api.get(BASE + "/admin/recetas/").data) == 2
    assert [r["title"] for r in api.get(BASE + "/admin/recetas/", {"status": "draft"}).data] == ["D"]


def test_reorder(cats, admin):
    a, b = make_recipe(cats, "A"), make_recipe(cats, "B")
    assert client(admin).post(BASE + "/admin/recetas/reorder/", {"ids": [b.id, a.id]}, format="json").status_code == 200
    assert [r["title"] for r in client().get(BASE + "/recetas/").data] == ["B", "A"]
    assert client(admin).post(BASE + "/admin/recetas/reorder/", {"ids": "x"}, format="json").status_code == 400


def test_guide_and_food_crud_sanitize_and_log(cats, admin):
    api = client(admin)
    g = api.post(
        BASE + "/admin/guias/",
        {"title": "Guía", "summary": "s", "content": "<p>ok</p><script>alert(1)</script>"},
        format="json",
    )
    assert g.status_code == 201 and "script" not in g.data["content"] and "alert" not in g.data["content"]
    f = api.post(
        BASE + "/admin/alimentos/",
        {"name": "Ejemplo", "age_range": cats["age"].id, "is_common_allergen": True, "allergen": cats["egg"].id},
        format="json",
    )
    assert f.status_code == 201
    assert FoodItem.objects.get(pk=f.data["id"]).is_common_allergen
    assert GuideArticle.objects.count() == 1
    assert ActivityLog.objects.filter(action="alimentacion_guide_created").exists()
    assert ActivityLog.objects.filter(action="alimentacion_food_created").exists()


def test_catalog_crud_and_protected_delete(cats, admin):
    api = client(admin)
    created = api.post(BASE + "/admin/alergenos/", {"name": "Pescado"}, format="json")
    assert created.status_code == 201 and created.data["slug"] == "pescado"
    assert api.patch(f"{BASE}/admin/alergenos/{created.data['id']}/", {"is_active": False}, format="json").status_code == 200
    make_recipe(cats)  # usa la edad 6-8
    in_use = api.delete(f"{BASE}/admin/edades/{cats['age'].id}/")
    assert in_use.status_code == 409
    assert AgeRange.objects.filter(pk=cats["age"].id).exists()
    assert api.delete(f"{BASE}/admin/alergenos/{created.data['id']}/").status_code == 204
    assert ActivityLog.objects.filter(action="alimentacion_allergen_created").exists()


def test_safety_admin_update_publish_rules(admin, madrina):
    r = client(admin).patch(
        BASE + "/admin/seguridad/",
        {"content": "<p>x</p>", "professional_name": "Dra. Ejemplo", "status": "published"},
        format="json",
    )
    assert r.status_code == 200
    assert client(madrina).patch(BASE + "/admin/seguridad/", {"status": "published"}, format="json").status_code == 403
    assert client(madrina).patch(BASE + "/admin/seguridad/", {"content": "<p>y</p>"}, format="json").status_code == 200
    assert ActivityLog.objects.filter(action="alimentacion_safety_updated").exists()


def test_safety_cannot_be_published_without_content_and_signature(admin):
    api = client(admin)
    assert api.patch(BASE + "/admin/seguridad/", {"status": "published"}, format="json").status_code == 400
    assert api.patch(BASE + "/admin/seguridad/", {"content": "<p>x</p>", "status": "published"}, format="json").status_code == 400
    assert SafetyContent.get_solo().status == "draft"
    ok = api.patch(BASE + "/admin/seguridad/", {"content": "<p>x</p>", "professional_name": "Dra. Ejemplo", "status": "published"}, format="json")
    assert ok.status_code == 200


# ---------- Imágenes ----------

def test_image_upload_validates_type_and_size(cats, admin, settings):
    r = make_recipe(cats)
    api = client(admin)
    ok = api.post(f"{BASE}/admin/recetas/{r.id}/image/", {"image": png()}, format="multipart")
    assert ok.status_code == 200 and ok.data["image"]
    bad = api.post(
        f"{BASE}/admin/recetas/{r.id}/image/",
        {"image": SimpleUploadedFile("a.gif", b"GIF89a", content_type="image/gif")},
        format="multipart",
    )
    assert bad.status_code == 400
    settings.MAX_IMAGE_UPLOAD_SIZE_MB = 0
    too_big = api.post(f"{BASE}/admin/recetas/{r.id}/image/", {"image": png()}, format="multipart")
    assert too_big.status_code == 400
    assert api.delete(f"{BASE}/admin/recetas/{r.id}/image/").status_code == 200
    r.refresh_from_db()
    assert not r.image


def test_image_upload_requires_edit_permission(cats, user):
    r = make_recipe(cats)
    assert client(user).post(f"{BASE}/admin/recetas/{r.id}/image/", {"image": png()}, format="multipart").status_code == 403
    assert client().post(f"{BASE}/admin/recetas/{r.id}/image/", {"image": png()}, format="multipart").status_code in (401, 403)


# ---------- Madrinas ----------

def test_module_access_payload_includes_alimentacion(madrina):
    from apps.access.services import module_access_payload

    payload = module_access_payload(madrina)
    assert payload["alimentacion"]["add"] is True and payload["alimentacion"]["approve"] is False


def test_can_assign_alimentacion_module_to_madrina():
    boss = User.objects.create_user(email="boss@example.com", password="x", is_staff=True, is_superuser=True)
    target = User.objects.create_user(email="nueva@example.com", password="x")
    api = client(boss)
    response = api.put(
        f"/api/admin/madrinas/{target.id}/",
        {"access": [{"module": "alimentacion", "can_add": True, "can_edit": True}]},
        format="json",
    )
    assert response.status_code == 200, response.data
    assert ModuleAccess.objects.filter(user=target, module="alimentacion", can_add=True).exists()
