from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import signing
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.businesses.models import Business, BusinessImage
from apps.categories.models import Category
from apps.core.models import ActivityLog, FeatureFlag
from apps.portal import services
from apps.portal.models import (
    BusinessBenefit,
    BusinessChangeLog,
    BusinessFAQ,
    BusinessOwner,
    CardVisit,
    DataSharingConsent,
    DiscountRedemption,
    Membership,
)
from apps.questions.models import Question
from apps.reviews.models import Review
from apps.users.models import Notification

User = get_user_model()
pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def portal_launched():
    FeatureFlag.objects.update_or_create(key="portal_module", defaults={"is_forced_active": True})


def make_user(email, **kwargs):
    kwargs.setdefault("is_active", True)
    return User.objects.create_user(email=email, password="ClaveSegura123", **kwargs)


def client_for(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def jwt_client_for(user):
    """Con token real: force_authenticate se salta la clase de autenticación (que bloquea cuentas solo-portal)."""
    from rest_framework_simplejwt.tokens import RefreshToken

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.fixture
def category():
    return Category.objects.create(name="Comida")


def make_business(category, owner, name="Negocio", **kwargs):
    return Business.objects.create(
        owner=owner, name=name, category=category, city="Cali", department="Valle",
        status=kwargs.pop("status", Business.Status.APPROVED), **kwargs,
    )


@pytest.fixture
def owner_a(category):
    user = make_user("duena-a@example.com", first_name="Ana", last_name="A", account_type="portal")
    business = make_business(category, user, "Negocio A")
    BusinessOwner.objects.create(user=user, business=business, role="owner")
    return user


@pytest.fixture
def owner_b(category):
    user = make_user("duena-b@example.com", first_name="Bea", last_name="B", account_type="portal")
    business = make_business(category, user, "Negocio B")
    BusinessOwner.objects.create(user=user, business=business, role="owner")
    return user


@pytest.fixture
def biz_a(owner_a):
    return owner_a.businesses.first()


@pytest.fixture
def biz_b(owner_b):
    return owner_b.businesses.first()


@pytest.fixture
def seller_a(biz_a):
    user = make_user("vendedora-a@example.com", first_name="Vera", account_type="portal")
    BusinessOwner.objects.create(user=user, business=biz_a, role="seller")
    return user


@pytest.fixture
def member():
    user = make_user("socia@example.com", first_name="Sofía", last_name="Soto", document_id="1234567890", whatsapp="+573001112233")
    DataSharingConsent.objects.create(user=user)
    return user


@pytest.fixture
def benefit_a(biz_a):
    return BusinessBenefit.objects.create(business=biz_a, percentage=15, status="approved")


def preview(owner, business, member_user=None, token=None, code=None):
    payload = {"token": token} if token else {"code": code}
    return client_for(owner).post(f"/api/portal/businesses/{business.id}/redeem/preview/", payload, format="json")


# ---------------------------------------------------------------- Acceso y aislamiento


def test_owner_sees_only_own_business(owner_a, biz_a, biz_b):
    response = client_for(owner_a).get("/api/portal/me/")
    assert [row["business_id"] for row in response.json()] == [biz_a.id]
    assert client_for(owner_a).get(f"/api/portal/businesses/{biz_a.id}/").status_code == 200


@pytest.mark.parametrize(
    "method,suffix",
    [
        ("get", ""), ("patch", ""), ("get", "images/"), ("get", "reviews/"), ("get", "questions/"),
        ("get", "faqs/"), ("get", "benefit/"), ("get", "stats/"), ("get", "members/"), ("get", "changes/"),
        ("post", "redeem/preview/"), ("post", "redeem/confirm/"), ("post", "faqs/"),
    ],
)
def test_owner_cannot_touch_another_business_by_changing_id(owner_a, biz_b, method, suffix):
    response = getattr(client_for(owner_a), method)(f"/api/portal/businesses/{biz_b.id}/{suffix}", {}, format="json")
    assert response.status_code == 404


def test_cannot_edit_or_delete_other_business_children_by_id(owner_a, biz_a, biz_b):
    faq_b = BusinessFAQ.objects.create(business=biz_b, question="¿Envían?", answer="Sí")
    image_b = BusinessImage.objects.create(business=biz_b, image="x.png")
    review_b = Review.objects.create(business=biz_b, user=owner_a, rating=5)
    question_b = Question.objects.create(business=biz_b, user=owner_a, question="Hola")
    api = client_for(owner_a)
    # Mismo ID de hijo pero a través de MI emprendimiento: no existe ahí.
    assert api.delete(f"/api/portal/businesses/{biz_a.id}/faqs/{faq_b.id}/").status_code == 404
    assert api.patch(f"/api/portal/businesses/{biz_a.id}/faqs/{faq_b.id}/", {"answer": "x"}, format="json").status_code == 404
    assert api.delete(f"/api/portal/businesses/{biz_a.id}/images/{image_b.id}/").status_code == 404
    assert api.put(f"/api/portal/businesses/{biz_a.id}/reviews/{review_b.id}/reply/", {"text": "x"}, format="json").status_code == 404
    assert api.post(f"/api/portal/businesses/{biz_a.id}/questions/{question_b.id}/answer/", {"answer": "x"}, format="json").status_code == 404
    assert BusinessFAQ.objects.filter(pk=faq_b.pk).exists()


def test_members_list_only_shows_own_business_users(owner_a, owner_b, biz_a, biz_b, member):
    CardVisit.objects.create(business=biz_b, user=member)
    response = client_for(owner_a).get(f"/api/portal/businesses/{biz_a.id}/members/")
    assert response.json()["count"] == 0
    CardVisit.objects.create(business=biz_a, user=member)
    response = client_for(owner_a).get(f"/api/portal/businesses/{biz_a.id}/members/")
    assert response.json()["count"] == 1


def test_unassigned_and_anonymous_users_are_blocked(biz_a, member):
    assert client_for(member).get(f"/api/portal/businesses/{biz_a.id}/").status_code == 404
    assert APIClient().get(f"/api/portal/businesses/{biz_a.id}/").status_code == 401


def test_pending_business_gives_no_portal_access(category):
    user = make_user("pend@example.com")
    business = make_business(category, user, status=Business.Status.PENDING)
    BusinessOwner.objects.create(user=user, business=business)
    assert client_for(user).get(f"/api/portal/businesses/{business.id}/").status_code == 404


def test_seller_can_read_stats_and_scan_but_not_edit(seller_a, biz_a):
    api = client_for(seller_a)
    assert api.get(f"/api/portal/businesses/{biz_a.id}/").status_code == 200
    assert api.get(f"/api/portal/businesses/{biz_a.id}/stats/").status_code == 200
    assert api.patch(f"/api/portal/businesses/{biz_a.id}/", {"name": "Hackeado"}, format="json").status_code == 403
    assert api.get(f"/api/portal/businesses/{biz_a.id}/faqs/").status_code == 403
    assert api.get(f"/api/portal/businesses/{biz_a.id}/members/").status_code == 403
    assert api.put(f"/api/portal/businesses/{biz_a.id}/benefit/", {"percentage": 10}, format="json").status_code == 403
    assert api.post(f"/api/portal/businesses/{biz_a.id}/redeem/preview/", {"code": "000000"}, format="json").status_code == 400


def test_multiple_owners_per_business(owner_a, seller_a, biz_a):
    assert BusinessOwner.objects.filter(business=biz_a).count() == 2


# ---------------------------------------------------------------- Mi emprendimiento


def test_edit_business_records_change_and_does_not_reset_status(owner_a, biz_a):
    response = client_for(owner_a).patch(
        f"/api/portal/businesses/{biz_a.id}/", {"name": "Nuevo nombre", "status": "pending", "average_rating": "5"}, format="json"
    )
    assert response.status_code == 200
    biz_a.refresh_from_db()
    assert biz_a.name == "Nuevo nombre"
    assert biz_a.status == "approved"  # el cliente no decide el estado
    log = BusinessChangeLog.objects.get(business=biz_a)
    assert log.changes["name"] == {"from": "Negocio A", "to": "Nuevo nombre"}
    assert log.actor == owner_a


def test_unchanged_edit_creates_no_log(owner_a, biz_a):
    client_for(owner_a).patch(f"/api/portal/businesses/{biz_a.id}/", {"name": biz_a.name}, format="json")
    assert not BusinessChangeLog.objects.exists()


# ---------------------------------------------------------------- Imágenes


def png(name="a.png"):
    from io import BytesIO

    from PIL import Image

    buffer = BytesIO()
    Image.new("RGB", (4, 4), "gold").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


def test_images_upload_reorder_main_and_delete(owner_a, biz_a, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    api = client_for(owner_a)
    url = f"/api/portal/businesses/{biz_a.id}/images/"
    first = api.post(url, {"image": png("1.png")}, format="multipart").json()
    second = api.post(url, {"image": png("2.png")}, format="multipart").json()
    assert first["is_main"] is True and second["is_main"] is False
    response = api.post(url + "reorder/", {"ids": [second["id"], first["id"]]}, format="json")
    assert response.status_code == 200
    listing = api.get(url).json()
    assert listing[0]["id"] == second["id"] and listing[0]["is_main"] is True
    assert api.post(url + "reorder/", {"ids": [second["id"]]}, format="json").status_code == 400  # incompleto
    assert api.delete(f"{url}{second['id']}/").status_code == 204
    assert api.get(url).json()[0]["id"] == first["id"]
    assert BusinessChangeLog.objects.filter(business=biz_a, entity="image").count() == 4


def test_images_reject_bad_type_and_limit(owner_a, biz_a, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    api = client_for(owner_a)
    url = f"/api/portal/businesses/{biz_a.id}/images/"
    bad = SimpleUploadedFile("a.gif", b"GIF89a", content_type="image/gif")
    assert api.post(url, {"image": bad}, format="multipart").status_code == 400
    for index in range(4):
        assert api.post(url, {"image": png(f"{index}.png")}, format="multipart").status_code == 201
    assert api.post(url, {"image": png("5.png")}, format="multipart").status_code == 400


# ---------------------------------------------------------------- Opiniones y preguntas


def test_reviews_are_read_only_but_owner_can_reply(owner_a, biz_a, member):
    review = Review.objects.create(business=biz_a, user=member, rating=4, comment="Rico")
    api = client_for(owner_a)
    base = f"/api/portal/businesses/{biz_a.id}/reviews/"
    assert api.get(base).json()["count"] == 1
    assert api.patch(f"{base}{review.id}/", {"comment": "x"}, format="json").status_code == 404
    assert api.delete(f"{base}{review.id}/").status_code == 404
    assert api.put(f"{base}{review.id}/reply/", {"text": "¡Gracias!"}, format="json").status_code == 200
    assert api.get(base).json()["results"][0]["reply"]["text"] == "¡Gracias!"
    public = APIClient().get(f"/api/businesses/{biz_a.id}/reviews/").json()["results"][0]
    assert public["reply"]["text"] == "¡Gracias!"
    assert api.delete(f"{base}{review.id}/reply/").status_code == 204
    review.refresh_from_db()
    assert review.comment == "Rico"


def test_owner_answers_question(owner_a, biz_a, member):
    question = Question.objects.create(business=biz_a, user=member, question="¿Hacen envíos?")
    response = client_for(owner_a).post(
        f"/api/portal/businesses/{biz_a.id}/questions/{question.id}/answer/", {"answer": "Sí"}, format="json"
    )
    assert response.status_code == 201
    assert response.json()["answer"]["answer"] == "Sí"


# ---------------------------------------------------------------- FAQ


def test_faq_crud_reorder_and_delete_are_logged(owner_a, biz_a):
    api = client_for(owner_a)
    url = f"/api/portal/businesses/{biz_a.id}/faqs/"
    one = api.post(url, {"question": "¿Envían?", "answer": "Sí"}, format="json").json()
    two = api.post(url, {"question": "¿Horario?", "answer": "9 a 5"}, format="json").json()
    assert api.patch(f"{url}{one['id']}/", {"answer": "Todo el país"}, format="json").status_code == 200
    assert api.post(url + "reorder/", {"ids": [two["id"], one["id"]]}, format="json").status_code == 200
    assert [f["id"] for f in api.get(url).json()] == [two["id"], one["id"]]
    assert api.delete(f"{url}{two['id']}/").status_code == 204
    actions = list(BusinessChangeLog.objects.filter(entity="faq").order_by("id").values_list("action", flat=True))
    assert actions == ["create", "create", "update", "delete"]


def test_public_detail_shows_faqs_and_only_approved_benefit(owner_a, biz_a):
    BusinessFAQ.objects.create(business=biz_a, question="¿Envían?", answer="Sí")
    BusinessBenefit.objects.create(business=biz_a, percentage=20, status="pending")
    detail = APIClient().get(f"/api/businesses/{biz_a.slug}/").json()
    assert detail["faqs"][0]["question"] == "¿Envían?"
    assert detail["portal_benefit"] is None
    BusinessBenefit.objects.filter(business=biz_a).update(status="approved")
    assert APIClient().get(f"/api/businesses/{biz_a.slug}/").json()["portal_benefit"]["percentage"] == 20


# ---------------------------------------------------------------- Beneficio


def test_benefit_validation_and_pending_approval_flow(owner_a, biz_a):
    api = client_for(owner_a)
    url = f"/api/portal/businesses/{biz_a.id}/benefit/"
    assert api.put(url, {"percentage": 0}, format="json").status_code == 400
    assert api.put(url, {"percentage": 101}, format="json").status_code == 400
    assert api.put(url, {"percentage": 10, "valid_from": "2026-12-10", "valid_until": "2026-12-01"}, format="json").status_code == 400
    response = api.put(url, {"percentage": 10, "conditions": "Presentando la tarjeta"}, format="json")
    assert response.status_code == 200 and response.json()["status"] == "pending"
    assert ActivityLog.objects.filter(action="benefit_submitted").count() == 1

    benefit = BusinessBenefit.objects.get(business=biz_a)
    admin = make_user("admin@example.com", is_staff=True)
    assert api.post(f"/api/admin/benefits/{benefit.id}/approve/").status_code == 403  # la dueña no aprueba
    assert client_for(admin).post(f"/api/admin/benefits/{benefit.id}/approve/").status_code == 200
    benefit.refresh_from_db()
    assert benefit.status == "approved" and benefit.reviewed_by == admin

    # Editar un beneficio aprobado vuelve a pendiente; reenviar lo mismo no.
    assert api.put(url, {"percentage": 10, "conditions": "Presentando la tarjeta"}, format="json").json()["status"] == "approved"
    assert api.put(url, {"percentage": 12, "conditions": "Presentando la tarjeta"}, format="json").json()["status"] == "pending"
    assert ActivityLog.objects.filter(action="benefit_approved").exists()
    assert BusinessChangeLog.objects.filter(business=biz_a, entity="benefit").count() >= 3


# ---------------------------------------------------------------- Estadísticas y usuarias


def test_stats_periods(owner_a, biz_a, member):
    now = timezone.now()
    for days in (0, 3, 20, 45):
        visit = CardVisit.objects.create(business=biz_a, user=member)
        CardVisit.objects.filter(pk=visit.pk).update(created_at=now - timedelta(days=days))
    DiscountRedemption.objects.create(user=member, business=biz_a, percentage=10, local_date=services.bogota_today())
    data = client_for(owner_a).get(f"/api/portal/businesses/{biz_a.id}/stats/").json()
    assert data["visits"] == {"today": 1, "last_7_days": 2, "last_30_days": 3, "total": 4}
    assert data["redemptions"]["total"] == 1


def test_card_visit_dedup_and_owner_visits_not_counted(owner_a, biz_a, member):
    api = client_for(member)
    assert api.post(f"/api/businesses/{biz_a.id}/card-visit/").status_code == 204
    api.post(f"/api/businesses/{biz_a.id}/card-visit/")
    assert CardVisit.objects.filter(business=biz_a).count() == 1
    client_for(owner_a).post(f"/api/businesses/{biz_a.id}/card-visit/")
    assert CardVisit.objects.filter(business=biz_a).count() == 1
    anon = APIClient()
    anon.post(f"/api/businesses/{biz_a.id}/card-visit/", {"session_id": "abc"}, format="json")
    anon.post(f"/api/businesses/{biz_a.id}/card-visit/", {"session_id": "abc"}, format="json")
    assert CardVisit.objects.filter(business=biz_a).count() == 2


def test_members_view_has_no_document_requires_consent_and_searches(owner_a, biz_a, member):
    CardVisit.objects.create(business=biz_a, user=member)
    no_consent = make_user("sin@example.com", first_name="Sin", document_id="999")
    CardVisit.objects.create(business=biz_a, user=no_consent)
    api = client_for(owner_a)
    data = api.get(f"/api/portal/businesses/{biz_a.id}/members/").json()
    assert data["count"] == 1  # la que no consintió no aparece
    row = data["results"][0]
    assert row["email"] == member.email and row["whatsapp"] == member.whatsapp
    assert "document_id" not in row and "1234567890" not in str(data)
    assert api.get(f"/api/portal/businesses/{biz_a.id}/members/?search=Soto").json()["count"] == 1
    assert api.get(f"/api/portal/businesses/{biz_a.id}/members/?search=nadie").json()["count"] == 0
    # Sin edición ni exportación: solo lectura
    assert api.post(f"/api/portal/businesses/{biz_a.id}/members/", {}, format="json").status_code == 405
    DataSharingConsent.objects.filter(user=member).update(revoked_at=timezone.now())
    assert api.get(f"/api/portal/businesses/{biz_a.id}/members/").json()["count"] == 0


# ---------------------------------------------------------------- Tarjeta / QR


def test_card_requires_document_and_consent(category):
    user = make_user("nueva@example.com", first_name="Nueva")
    data = client_for(user).get("/api/me/card/").json()
    assert data["eligible"] is False and "token" not in data
    assert set(data["blockers"]) == {"missing_document", "consent_required"}
    user.document_id = "555"
    user.save()
    assert client_for(user).post("/api/me/card/consent/", {"accepted": True}, format="json").status_code == 201
    data = client_for(user).get("/api/me/card/").json()
    assert data["eligible"] is True and data["expires_in"] == 90 and len(data["code"]) == 6
    assert DataSharingConsent.objects.get(user=user).accepted_at


def test_consent_must_be_explicit_and_can_be_revoked(member):
    api = client_for(make_user("c@example.com", document_id="77"))
    assert api.post("/api/me/card/consent/", {}, format="json").status_code == 400
    api.post("/api/me/card/consent/", {"accepted": True}, format="json")
    assert api.delete("/api/me/card/consent/").status_code == 204
    assert "consent_required" in api.get("/api/me/card/").json()["blockers"]


def test_token_has_no_personal_data(member):
    token = client_for(member).get("/api/me/card/").json()["token"]
    for secret in (member.email, member.document_id, member.first_name, member.whatsapp):
        assert secret not in token


def test_redeem_happy_path_scan_and_code(owner_a, biz_a, member, benefit_a):
    card = client_for(member).get("/api/me/card/").json()
    response = preview(owner_a, biz_a, token=card["token"])
    assert response.status_code == 200
    body = response.json()
    assert body["member"] == {"name": "Sofía Soto", "status": "Activa"}
    assert body["benefit"]["percentage"] == 15
    confirm = client_for(owner_a).post(
        f"/api/portal/businesses/{biz_a.id}/redeem/confirm/", {"ticket": body["ticket"]}, format="json"
    )
    assert confirm.status_code == 201
    redemption = DiscountRedemption.objects.get()
    assert redemption.percentage == 15 and redemption.redeemed_by == owner_a
    assert ActivityLog.objects.filter(action="discount_redeemed").exists()
    assert "Se aplicó tu descuento" in client_for(member).get("/api/me/notices/").json()["results"][0]["message"]
    # el mismo día no se repite, ni por QR ni por código
    again = preview(owner_a, biz_a, code=card["code"])
    assert again.status_code == 400 and again.json()["detail"] == "Descuento ya usado hoy."


def test_seller_can_redeem(seller_a, biz_a, member, benefit_a):
    card = client_for(member).get("/api/me/card/").json()
    ticket = preview(seller_a, biz_a, token=card["token"]).json()["ticket"]
    response = client_for(seller_a).post(f"/api/portal/businesses/{biz_a.id}/redeem/confirm/", {"ticket": ticket}, format="json")
    assert response.status_code == 201


def test_expired_token_is_rejected(owner_a, biz_a, member, benefit_a, monkeypatch):
    import time

    token = signing.TimestampSigner(salt=services.CARD_SALT).sign(str(member.pk))
    real = time.time()
    monkeypatch.setattr(time, "time", lambda: real + 91)
    assert preview(owner_a, biz_a, token=token).json()["code"] == "expired"


def test_tampered_or_foreign_token_is_rejected(owner_a, biz_a, member, benefit_a):
    token = client_for(member).get("/api/me/card/").json()["token"]
    forged = token.replace(f"{member.pk}:", "9999:", 1)
    assert preview(owner_a, biz_a, token=forged).json()["code"] == "invalid"
    assert preview(owner_a, biz_a, token="basura").json()["code"] == "invalid"
    other_salt = signing.TimestampSigner(salt="otra").sign(str(member.pk))
    assert preview(owner_a, biz_a, token=other_salt).json()["code"] == "invalid"


def test_expired_backup_code(owner_a, biz_a, member, benefit_a):
    card = client_for(member).get("/api/me/card/").json()
    member.card_code.__class__.objects.filter(user=member).update(expires_at=timezone.now() - timedelta(seconds=1))
    assert preview(owner_a, biz_a, code=card["code"]).json()["code"] == "expired"
    assert preview(owner_a, biz_a, code="000000").json()["code"] == "invalid"


def test_inactive_account_message(owner_a, biz_a, member, benefit_a):
    token = client_for(member).get("/api/me/card/").json()["token"]
    member.is_active = False
    member.save()
    response = preview(owner_a, biz_a, token=token)
    assert response.status_code == 400 and response.json()["detail"] == "Cuenta inactiva."


def test_membership_can_be_suspended_by_admin(owner_a, biz_a, member, benefit_a):
    admin = make_user("admin@example.com", is_staff=True)
    token = client_for(member).get("/api/me/card/").json()["token"]
    assert preview(owner_a, biz_a, token=token).status_code == 200  # activa por defecto, sin fila
    api = client_for(admin)
    assert api.get("/api/admin/memberships/").status_code == 200
    assert api.patch(f"/api/admin/memberships/{member.id}/set/", {"is_active": False}, format="json").status_code == 200
    assert Membership.objects.get(user=member).is_active is False
    assert preview(owner_a, biz_a, token=token).json()["detail"] == "Membresía inactiva."
    assert client_for(member).get("/api/me/card/").json()["blockers"] == ["membership_inactive"]
    assert client_for(owner_a).get("/api/admin/memberships/").status_code == 403


def test_redeem_needs_valid_approved_benefit(owner_a, biz_a, member):
    token = client_for(member).get("/api/me/card/").json()["token"]
    assert preview(owner_a, biz_a, token=token).json()["code"] == "no_benefit"
    benefit = BusinessBenefit.objects.create(business=biz_a, percentage=10, status="pending")
    assert preview(owner_a, biz_a, token=token).json()["code"] == "no_benefit"
    benefit.status = "approved"
    benefit.valid_until = services.bogota_today() - timedelta(days=1)
    benefit.save()
    assert preview(owner_a, biz_a, token=token).json()["code"] == "no_benefit"


def test_redeem_needs_consent(owner_a, biz_a, member, benefit_a):
    token = client_for(member).get("/api/me/card/").json()["token"]
    DataSharingConsent.objects.filter(user=member).update(revoked_at=timezone.now())
    assert preview(owner_a, biz_a, token=token).json()["code"] == "no_consent"


def test_duplicate_is_blocked_by_database_even_if_confirmed_twice(owner_a, biz_a, member, benefit_a):
    token = client_for(member).get("/api/me/card/").json()["token"]
    ticket = preview(owner_a, biz_a, token=token).json()["ticket"]
    api = client_for(owner_a)
    url = f"/api/portal/businesses/{biz_a.id}/redeem/confirm/"
    assert api.post(url, {"ticket": ticket}, format="json").status_code == 201
    second = api.post(url, {"ticket": ticket}, format="json")
    assert second.status_code == 400 and second.json()["detail"] == "Descuento ya usado hoy."
    assert DiscountRedemption.objects.count() == 1


def test_discount_from_one_business_does_not_block_another(owner_a, owner_b, biz_a, biz_b, member, benefit_a):
    BusinessBenefit.objects.create(business=biz_b, percentage=5, status="approved")
    token = client_for(member).get("/api/me/card/").json()["token"]
    for owner, business in ((owner_a, biz_a), (owner_b, biz_b)):
        ticket = preview(owner, business, token=token).json()["ticket"]
        url = f"/api/portal/businesses/{business.id}/redeem/confirm/"
        assert client_for(owner).post(url, {"ticket": ticket}, format="json").status_code == 201


def test_ticket_is_bound_to_business(owner_a, owner_b, biz_a, biz_b, member, benefit_a):
    token = client_for(member).get("/api/me/card/").json()["token"]
    ticket = preview(owner_a, biz_a, token=token).json()["ticket"]
    response = client_for(owner_b).post(f"/api/portal/businesses/{biz_b.id}/redeem/confirm/", {"ticket": ticket}, format="json")
    assert response.status_code == 400 and not DiscountRedemption.objects.exists()


def test_redeem_endpoint_is_rate_limited(owner_a, biz_a, settings):
    from rest_framework.throttling import ScopedRateThrottle

    from django.core.cache import cache

    cache.clear()
    ScopedRateThrottle.THROTTLE_RATES = {**ScopedRateThrottle.THROTTLE_RATES, "portal_redeem": "3/min"}
    try:
        api = client_for(owner_a)
        url = f"/api/portal/businesses/{biz_a.id}/redeem/preview/"
        codes = [api.post(url, {"code": "111111"}, format="json").status_code for _ in range(5)]
        assert codes[-1] == 429
    finally:
        ScopedRateThrottle.THROTTLE_RATES = {**ScopedRateThrottle.THROTTLE_RATES, "portal_redeem": "30/min"}
        cache.clear()


# ---------------------------------------------------------------- Cuentas portal / member


def test_portal_account_is_blocked_outside_portal(owner_a, biz_a):
    api = jwt_client_for(owner_a)
    assert api.get("/api/me/").status_code == 200
    assert api.get("/api/portal/me/").status_code == 200
    assert api.get("/api/businesses/").status_code == 200
    assert api.get("/api/categories/").status_code == 200
    assert api.post("/api/businesses/", {}, format="json").status_code in (403, 405)
    assert api.get("/api/blog/").status_code == 403
    assert api.get("/api/news/").status_code == 403
    assert api.get("/api/festejos/").status_code == 403
    assert api.post(f"/api/businesses/{biz_a.id}/favorite/").status_code == 403
    assert api.post(f"/api/businesses/{biz_a.id}/reviews/", {"rating": 5}, format="json").status_code == 403


def test_member_with_business_has_portal_and_site(category):
    user = make_user("socia-duena@example.com")
    business = make_business(category, user)
    BusinessOwner.objects.create(user=user, business=business)
    api = client_for(user)
    assert api.get(f"/api/portal/businesses/{business.id}/").status_code == 200
    assert api.get("/api/news/").status_code == 200
    assert api.get("/api/me/").json()["has_portal_access"] is True


def test_portal_registration_inactive_until_approved_then_convert(biz_a):
    anon = APIClient()
    payload = {
        "email": "nueva-portal@example.com", "password": "ClaveSegura123", "first_name": "Nora", "last_name": "N",
        "whatsapp": "+573001234567", "business_name": "Mi Negocio",
    }
    assert anon.post("/api/auth/register-portal/", payload, format="json").status_code == 201
    user = User.objects.get(email="nueva-portal@example.com")
    assert user.account_type == "portal" and user.is_active is False
    assert Notification.objects.filter(related_user=user).exists()
    assert anon.post("/api/auth/login/", {"email": user.email, "password": "ClaveSegura123"}, format="json").status_code == 401

    admin = make_user("admin@example.com", is_staff=True)
    api = client_for(admin)
    assert api.patch(f"/api/admin/users/{user.id}/", {"is_approved": True}, format="json").status_code == 200
    user.refresh_from_db()
    assert user.is_active and user.is_approved  # aprobar también activa la cuenta
    created = api.post("/api/admin/business-owners/", {"user": user.id, "business": biz_a.id, "role": "seller"}, format="json")
    assert created.status_code == 201
    assert client_for(user).get("/api/portal/me/").json()[0]["role"] == "seller"
    assert ActivityLog.objects.filter(action="portal_access_assigned").exists()

    # Pide pasar a usuaria de la página; un admin lo convierte.
    assert client_for(user).post("/api/me/request-member-conversion/").status_code == 202
    assert Notification.objects.filter(type="member_conversion_request", related_user=user).count() == 1
    client_for(user).post("/api/me/request-member-conversion/")
    assert Notification.objects.filter(type="member_conversion_request", related_user=user).count() == 1
    assert jwt_client_for(user).get("/api/news/").status_code == 403
    assert api.post(f"/api/admin/users/{user.id}/convert_to_member/").status_code == 200
    user.refresh_from_db()
    assert user.account_type == "member"
    assert jwt_client_for(user).get("/api/news/").status_code == 200
    assert ActivityLog.objects.filter(action="account_converted_to_member").exists()
    assert client_for(make_user("x@example.com")).post(f"/api/admin/users/{user.id}/convert_to_member/").status_code == 403


def test_assigning_requires_approved_business_and_active_user(category, owner_a):
    admin = make_user("admin@example.com", is_staff=True)
    pending = make_business(category, admin, "Pendiente", status=Business.Status.PENDING)
    inactive = make_user("inactiva@example.com", is_active=False)
    api = client_for(admin)
    assert api.post("/api/admin/business-owners/", {"user": owner_a.id, "business": pending.id}, format="json").status_code == 400
    approved = make_business(category, admin, "Aprobado")
    assert api.post("/api/admin/business-owners/", {"user": inactive.id, "business": approved.id}, format="json").status_code == 400
    assert client_for(owner_a).post("/api/admin/business-owners/", {"user": owner_a.id, "business": approved.id}, format="json").status_code == 403


def test_seed_migration_style_assignment_for_existing_owner(category):
    """Quien ya es Business.owner de un emprendimiento aprobado conserva su acceso (la migración lo siembra)."""
    from importlib import import_module

    user = make_user("vieja@example.com")
    business = make_business(category, user)
    from django.apps import apps

    import_module("apps.portal.migrations.0002_seed_owners_from_business_owner").seed_owners(apps, None)
    assert BusinessOwner.objects.filter(user=user, business=business, role="owner").exists()


# ---------------------------------------------------------------- Lanzamiento (FeatureFlag)


def test_before_launch_normal_users_see_nothing_but_admin_does(owner_a, biz_a, member, benefit_a):
    FeatureFlag.objects.filter(key="portal_module").update(is_forced_active=False, activate_at=None)
    BusinessFAQ.objects.create(business=biz_a, question="¿Envían?", answer="Sí")
    assert client_for(owner_a).get("/api/portal/me/").status_code == 404
    assert client_for(owner_a).get(f"/api/portal/businesses/{biz_a.id}/").status_code == 404
    assert client_for(member).get("/api/me/card/").status_code == 404
    assert APIClient().post("/api/auth/register-portal/", {}, format="json").status_code == 404
    client_for(member).post(f"/api/businesses/{biz_a.id}/card-visit/")
    assert not CardVisit.objects.exists()
    detail = APIClient().get(f"/api/businesses/{biz_a.slug}/").json()
    assert detail["faqs"] == [] and detail["portal_benefit"] is None
    admin = make_user("admin@example.com", is_staff=True)
    assert client_for(admin).get("/api/me/card/").status_code == 200
    assert client_for(admin).post(f"/api/businesses/{biz_a.id}/card-visit/").status_code == 204
    assert CardVisit.objects.count() == 1
    FeatureFlag.objects.filter(key="portal_module").update(is_forced_active=True)
    assert client_for(owner_a).get("/api/portal/me/").status_code == 200


def test_existing_roles_unchanged(member):
    api = client_for(member)
    assert api.get("/api/admin/users/").status_code == 403
    assert api.get("/api/admin/business-owners/").status_code == 403
