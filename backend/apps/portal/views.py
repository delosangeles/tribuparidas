from datetime import timedelta

from django.db import IntegrityError, transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.db.models.functions import Coalesce, Greatest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import filters, generics, mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.businesses.models import Business, BusinessImage
from apps.businesses.views import MAX_IMAGES_PER_BUSINESS
from apps.core.models import log_activity
from apps.questions.models import Answer, Question
from apps.questions.serializers import QuestionSerializer
from apps.reviews.models import Review
from apps.users.models import Notification, User

from .models import (
    CONSENT_VERSION,
    BusinessBenefit,
    BusinessChangeLog,
    BusinessFAQ,
    BusinessOwner,
    CardVisit,
    DataSharingConsent,
    DiscountRedemption,
    MemberNotice,
    Membership,
    ReviewReply,
)
from .permissions import PortalBusinessMixin, PortalModuleLive
from .serializers import (
    AdminBenefitSerializer,
    BenefitSerializer,
    BusinessOwnerSerializer,
    ChangeLogSerializer,
    FAQSerializer,
    MemberNoticeSerializer,
    MemberRowSerializer,
    PortalBusinessSerializer,
    PortalImageSerializer,
    PortalRegisterSerializer,
    PortalReviewSerializer,
    ReplySerializer,
)
from .services import (
    BOGOTA,
    CardError,
    active_consent,
    bogota_today,
    card_blockers,
    diff_fields,
    has_active_membership,
    is_portal_module_live,
    issue_code,
    issue_token,
    log_change,
    make_ticket,
    read_ticket,
    resolve_user,
    TOKEN_TTL_SECONDS,
    validate_redemption,
)

VISIT_DEDUP_MINUTES = 30


class NoPagination:
    pagination_class = None


# ---------------------------------------------------------------- Portal


class PortalMeView(APIView):
    """GET /api/portal/me/ — emprendimientos a los que la persona tiene acceso."""

    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]

    def get(self, request):
        rows = BusinessOwner.objects.filter(user=request.user, business__status="approved").select_related("business")
        return Response(
            [
                {
                    "business_id": row.business_id,
                    "name": row.business.name,
                    "slug": row.business.slug,
                    "role": row.role,
                    "logo": request.build_absolute_uri(row.business.logo.url) if row.business.logo else None,
                }
                for row in rows
            ]
        )


class PortalBusinessView(PortalBusinessMixin, generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/portal/businesses/<id>/ — mi emprendimiento."""

    serializer_class = PortalBusinessSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.business

    def perform_update(self, serializer):
        business = serializer.instance
        changes = diff_fields(business, serializer.validated_data)
        # La categoría se compara por nombre, no por id, para que el historial se lea bien.
        if "category" in changes:
            changes["category"] = {"from": business.category.name, "to": serializer.validated_data["category"].name}
        serializer.save()
        if changes:
            log_change(business, self.request.user, "business", "update", changes)


class PortalImageViewSet(PortalBusinessMixin, NoPagination, viewsets.ModelViewSet):
    """/api/portal/businesses/<id>/images/ — la imagen principal es la primera del orden."""

    serializer_class = PortalImageSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return BusinessImage.objects.filter(business=self.business)

    def perform_create(self, serializer):
        count = self.business.images.count()
        if count >= MAX_IMAGES_PER_BUSINESS:
            raise serializers.ValidationError({"image": f"Máximo {MAX_IMAGES_PER_BUSINESS} imágenes por emprendimiento."})
        last = self.business.images.order_by("-order").first()
        image = serializer.save(business=self.business, order=(last.order + 1) if last else 0)
        log_change(self.business, self.request.user, "image", "create", {"image": {"from": None, "to": image.image.name}})

    def perform_update(self, serializer):
        changes = diff_fields(serializer.instance, serializer.validated_data)
        serializer.save()
        if changes:
            log_change(self.business, self.request.user, "image", "update", changes)

    def perform_destroy(self, instance):
        name = instance.image.name
        instance.delete()
        log_change(self.business, self.request.user, "image", "delete", {"image": {"from": name, "to": None}})

    @action(detail=False, methods=["post"])
    def reorder(self, request, business_id=None):
        """Body: {"ids": [3, 1, 2]} — el primero queda como imagen principal."""
        ids = request.data.get("ids")
        current = set(self.business.images.values_list("id", flat=True))
        if not isinstance(ids, list) or set(ids) != current or len(ids) != len(current):
            return Response({"detail": "Envía todas las imágenes del emprendimiento, una sola vez cada una."}, status=400)
        with transaction.atomic():
            for position, pk in enumerate(ids):
                BusinessImage.objects.filter(pk=pk, business=self.business).update(order=position)
        log_change(self.business, request.user, "image", "reorder", {"order": {"from": None, "to": ids}})
        return Response(self.get_serializer(self.get_queryset(), many=True).data)


class PortalReviewListView(PortalBusinessMixin, generics.ListAPIView):
    """GET — opiniones recibidas (solo lectura). La dueña puede responderlas."""

    owner_only = True
    serializer_class = PortalReviewSerializer
    ordering_fields = ["created_at", "rating"]

    def get_queryset(self):
        return Review.objects.filter(business=self.business, is_active=True).select_related("user", "reply")


class PortalReviewReplyView(PortalBusinessMixin, APIView):
    """PUT/DELETE /api/portal/businesses/<id>/reviews/<review_id>/reply/"""

    owner_only = True

    def get_review(self, review_id):
        return get_object_or_404(Review, pk=review_id, business=self.business, is_active=True)

    def put(self, request, business_id, review_id):
        review = self.get_review(review_id)
        serializer = ReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        previous = getattr(review, "reply", None)
        reply, _ = ReviewReply.objects.update_or_create(
            review=review, defaults={"text": serializer.validated_data["text"], "author": request.user}
        )
        log_change(
            self.business, request.user, "review_reply", "update" if previous else "create",
            {"text": {"from": previous.text if previous else None, "to": reply.text}},
        )
        return Response(PortalReviewSerializer(review).data)

    def delete(self, request, business_id, review_id):
        review = self.get_review(review_id)
        reply = getattr(review, "reply", None)
        if reply is None:
            return Response(status=404)
        log_change(self.business, request.user, "review_reply", "delete", {"text": {"from": reply.text, "to": None}})
        reply.delete()
        return Response(status=204)


class PortalQuestionListView(PortalBusinessMixin, generics.ListAPIView):
    """GET — preguntas que hizo la gente sobre el emprendimiento."""

    owner_only = True
    serializer_class = QuestionSerializer

    def get_queryset(self):
        return Question.objects.filter(business=self.business, is_active=True).select_related("user", "business", "answer")


class PortalQuestionAnswerView(PortalBusinessMixin, APIView):
    owner_only = True

    def post(self, request, business_id, question_id):
        question = get_object_or_404(Question, pk=question_id, business=self.business, is_active=True)
        text = str(request.data.get("answer", "")).strip()
        if not text:
            return Response({"answer": ["Escribe una respuesta."]}, status=400)
        Answer.objects.update_or_create(question=question, defaults={"answer": text, "user": request.user})
        question.refresh_from_db()
        return Response(QuestionSerializer(question).data, status=201)


class PortalFAQViewSet(PortalBusinessMixin, NoPagination, viewsets.ModelViewSet):
    """Preguntas frecuentes del emprendimiento (la dueña crea, edita, ordena y borra)."""

    owner_only = True
    serializer_class = FAQSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return BusinessFAQ.objects.filter(business=self.business)

    def perform_create(self, serializer):
        last = self.business.faqs.order_by("-order").first()
        faq = serializer.save(business=self.business, order=(last.order + 1) if last else 0)
        log_change(self.business, self.request.user, "faq", "create", {"question": {"from": None, "to": faq.question}})

    def perform_update(self, serializer):
        changes = diff_fields(serializer.instance, {k: v for k, v in serializer.validated_data.items() if k != "order"})
        serializer.save()
        if changes:
            log_change(self.business, self.request.user, "faq", "update", changes)

    def perform_destroy(self, instance):
        log_change(
            self.business, self.request.user, "faq", "delete",
            {"question": {"from": instance.question, "to": None}, "answer": {"from": instance.answer, "to": None}},
        )
        instance.delete()

    @action(detail=False, methods=["post"])
    def reorder(self, request, business_id=None):
        ids = request.data.get("ids")
        current = set(self.business.faqs.values_list("id", flat=True))
        if not isinstance(ids, list) or set(ids) != current or len(ids) != len(current):
            return Response({"detail": "Envía todas las preguntas, una sola vez cada una."}, status=400)
        with transaction.atomic():
            for position, pk in enumerate(ids):
                BusinessFAQ.objects.filter(pk=pk, business=self.business).update(order=position)
        return Response(self.get_serializer(self.get_queryset(), many=True).data)


class PortalBenefitView(PortalBusinessMixin, APIView):
    """GET/PUT — Beneficio Tribu. Cada cambio real vuelve a "pendiente" hasta
    que un admin lo apruebe."""

    owner_only = True

    def get(self, request, business_id):
        benefit = BusinessBenefit.objects.filter(business=self.business).first()
        return Response(BenefitSerializer(benefit).data if benefit else None)

    @transaction.atomic
    def put(self, request, business_id):
        benefit = BusinessBenefit.objects.filter(business=self.business).first()
        serializer = BenefitSerializer(benefit, data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if benefit is None:
            benefit = serializer.save(business=self.business, status=BusinessBenefit.Status.PENDING)
            changes = {k: {"from": None, "to": str(v)} for k, v in data.items()}
            verb, action_ = "creó", "create"
        else:
            changes = diff_fields(benefit, data)
            if not changes:
                return Response(BenefitSerializer(benefit).data)
            benefit = serializer.save(status=BusinessBenefit.Status.PENDING, reviewed_by=None, reviewed_at=None)
            verb, action_ = "editó", "update"
        log_change(self.business, request.user, "benefit", action_, changes)
        log_activity(
            request.user, "benefit_submitted",
            f"{request.user.email} {verb} el beneficio de «{self.business.name}» ({benefit.percentage}%): pendiente de aprobación.",
            target=self.business,
        )
        return Response(BenefitSerializer(benefit).data)


class PortalChangeLogView(PortalBusinessMixin, generics.ListAPIView):
    """Historial de cambios del emprendimiento."""

    owner_only = True
    serializer_class = ChangeLogSerializer

    def get_queryset(self):
        return BusinessChangeLog.objects.filter(business=self.business).select_related("actor")


def _period_counts(queryset):
    now = timezone.now()
    today = now.astimezone(BOGOTA).replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "today": queryset.filter(created_at__gte=today).count(),
        "last_7_days": queryset.filter(created_at__gte=today - timedelta(days=6)).count(),
        "last_30_days": queryset.filter(created_at__gte=today - timedelta(days=29)).count(),
        "total": queryset.count(),
    }


class PortalStatsView(PortalBusinessMixin, APIView):
    """Visitas a la tarjeta y descuentos aplicados (hoy, 7 días, 30 días, total)."""

    def get(self, request, business_id):
        return Response(
            {
                "visits": _period_counts(CardVisit.objects.filter(business=self.business)),
                "redemptions": _period_counts(DiscountRedemption.objects.filter(business=self.business)),
            }
        )


class PortalMembersView(PortalBusinessMixin, generics.ListAPIView):
    """Usuarias que abrieron la tarjeta o canjearon, SOLO las que dieron su
    consentimiento. Sin cédula, sin edición, sin exportación."""

    owner_only = True
    serializer_class = MemberRowSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["first_name", "last_name", "email", "whatsapp"]

    def get_queryset(self):
        business = self.business
        visits = CardVisit.objects.filter(business=business, user=OuterRef("pk")).order_by("-created_at")
        redemptions = DiscountRedemption.objects.filter(business=business, user=OuterRef("pk")).order_by("-created_at")
        return (
            User.objects.filter(
                Q(pk__in=CardVisit.objects.filter(business=business, user__isnull=False).values("user"))
                | Q(pk__in=DiscountRedemption.objects.filter(business=business).values("user")),
                data_sharing_consent__isnull=False,
                data_sharing_consent__revoked_at__isnull=True,
            )
            .annotate(
                last_visit=Subquery(visits.values("created_at")[:1]),
                last_redemption=Subquery(redemptions.values("created_at")[:1]),
                redemption_count=Count("redemptions", filter=Q(redemptions__business=business)),
            )
            .annotate(
                last_activity=Greatest(
                    Coalesce("last_visit", "last_redemption"), Coalesce("last_redemption", "last_visit")
                )
            )
            .order_by("-last_activity", "id")
        )


# ------------------------------------------------------- Canje con QR


def _card_error_response(error, user=None):
    body = {"code": error.code, "detail": error.message}
    if user is not None:
        body["member"] = {"name": user.get_full_name()}
    return Response(body, status=status.HTTP_400_BAD_REQUEST)


class RedeemPreviewView(PortalBusinessMixin, APIView):
    """POST {token | code} — valida el QR y muestra nombre, estado y beneficio."""

    write_requires_owner = False  # las vendedoras también escanean
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "portal_redeem"

    def post(self, request, business_id):
        user = None
        try:
            user = resolve_user(request.data.get("token"), request.data.get("code"))
            benefit = validate_redemption(user, self.business)
        except CardError as error:
            return _card_error_response(error, user)
        return Response(
            {
                "member": {"name": user.get_full_name(), "status": "Activa"},
                "benefit": {"percentage": benefit.percentage, "conditions": benefit.conditions},
                "ticket": make_ticket(user, self.business),
            }
        )


class RedeemConfirmView(PortalBusinessMixin, APIView):
    """POST {ticket} — registra el canje. La restricción única de la base de
    datos impide dos canjes el mismo día aunque lleguen a la vez."""

    write_requires_owner = False
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "portal_redeem"

    def post(self, request, business_id):
        user = None
        try:
            user = read_ticket(request.data.get("ticket", ""), self.business)
            benefit = validate_redemption(user, self.business)
            with transaction.atomic():
                redemption = DiscountRedemption.objects.create(
                    user=user,
                    business=self.business,
                    percentage=benefit.percentage,
                    redeemed_by=request.user,
                    local_date=bogota_today(),
                )
        except CardError as error:
            return _card_error_response(error, user)
        except IntegrityError:
            return _card_error_response(CardError("already_used", "Descuento ya usado hoy."), user)
        MemberNotice.objects.create(
            user=user, message=f"Se aplicó tu descuento del {redemption.percentage}% en {self.business.name}. ¡Disfrútalo!"
        )
        log_activity(
            request.user, "discount_redeemed",
            f"{request.user.email} aplicó {redemption.percentage}% a {user.get_full_name()} en «{self.business.name}».",
            target=self.business,
        )
        return Response(
            {"detail": "Descuento aplicado.", "percentage": redemption.percentage, "member": {"name": user.get_full_name()}},
            status=status.HTTP_201_CREATED,
        )


# ------------------------------------------------------ Usuaria: tarjeta


class MyCardView(APIView):
    """GET /api/me/card/ — QR dinámico (token firmado de 90 s) y código de respaldo."""

    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "card_issue"

    def get(self, request):
        user = request.user
        blockers = card_blockers(user)
        today = bogota_today()
        benefits = []
        for benefit in BusinessBenefit.objects.filter(business__status="approved").select_related("business"):
            if benefit.is_valid_on(today):
                business = benefit.business
                benefits.append(
                    {
                        "business_id": business.pk,
                        "name": business.name,
                        "slug": business.slug,
                        "logo": request.build_absolute_uri(business.logo.url) if business.logo else None,
                        "percentage": benefit.percentage,
                        "conditions": benefit.conditions,
                        "valid_until": benefit.valid_until,
                    }
                )
        data = {
            "eligible": not blockers,
            "blockers": blockers,
            "name": user.get_full_name(),
            "membership_active": has_active_membership(user),
            "consent_version": CONSENT_VERSION,
            "benefits": benefits,
        }
        if not blockers:
            data.update({"token": issue_token(user), "code": issue_code(user), "expires_in": TOKEN_TTL_SECONDS})
        return Response(data)


class MyCardConsentView(APIView):
    """POST acepta compartir datos con los emprendimientos; DELETE lo revoca."""

    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]

    def post(self, request):
        if request.data.get("accepted") is not True:
            return Response({"detail": "Debes aceptar para activar tu tarjeta."}, status=400)
        consent, created = DataSharingConsent.objects.get_or_create(user=request.user)
        if not created:
            consent.version = CONSENT_VERSION
            consent.revoked_at = None
            consent.accepted_at = timezone.now()
            consent.save()
        return Response({"accepted_at": consent.accepted_at, "version": consent.version}, status=201)

    def delete(self, request):
        updated = DataSharingConsent.objects.filter(user=request.user, revoked_at__isnull=True).update(
            revoked_at=timezone.now()
        )
        return Response(status=204 if updated else 404)


class MyNoticesView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]
    serializer_class = MemberNoticeSerializer

    def get_queryset(self):
        return MemberNotice.objects.filter(user=self.request.user)


class MyNoticesReadView(APIView):
    permission_classes = [permissions.IsAuthenticated, PortalModuleLive]

    def post(self, request):
        MemberNotice.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response(status=204)


class CardVisitView(APIView):
    """POST /api/businesses/<id>/card-visit/ — se llama al abrir la tarjeta pública."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "card_visit"

    def post(self, request, business_id):
        business = get_object_or_404(Business, pk=business_id, status=Business.Status.APPROVED)
        if not is_portal_module_live() and not (request.user.is_authenticated and request.user.is_staff):
            return Response(status=204)
        user = request.user if request.user.is_authenticated else None
        if user and BusinessOwner.objects.filter(user=user, business=business).exists():
            return Response(status=204)  # las visitas del propio equipo no cuentan
        session_id = str(request.data.get("session_id", ""))[:40]
        recent = CardVisit.objects.filter(
            business=business, created_at__gte=timezone.now() - timedelta(minutes=VISIT_DEDUP_MINUTES)
        )
        if user:
            duplicated = recent.filter(user=user).exists()
        elif session_id:
            duplicated = recent.filter(user__isnull=True, session_id=session_id).exists()
        else:
            duplicated = False
        if not duplicated:
            CardVisit.objects.create(business=business, user=user, session_id=session_id)
        return Response(status=204)


# ------------------------------------------------------------ Cuentas portal


class PortalRegisterView(generics.CreateAPIView):
    """POST /api/auth/register-portal/ — cuenta solo-portal, inactiva hasta que un admin la aprueba y la asigna."""

    serializer_class = PortalRegisterSerializer
    permission_classes = [permissions.AllowAny, PortalModuleLive]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        business_name = data.pop("business_name")
        password = data.pop("password")
        user = User.objects.create_user(**data, password=password, is_active=False, account_type="portal")
        Notification.objects.create(
            type=Notification.Type.NEW_REGISTRATION,
            related_user=user,
            message=f"{user.get_full_name()} ({user.email}) pidió acceso al portal para «{business_name}».",
        )
        return Response(
            {"detail": "¡Solicitud recibida! Un administrador revisará tu cuenta y te asignará tu emprendimiento."},
            status=status.HTTP_201_CREATED,
        )


class RequestMemberConversionView(APIView):
    """POST /api/me/request-member-conversion/ — una cuenta portal pide pasar a usuaria de la página."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.account_type != "portal":
            return Response({"detail": "Tu cuenta ya es de usuaria de la página."}, status=400)
        pending = Notification.objects.filter(
            type=Notification.Type.MEMBER_CONVERSION_REQUEST, related_user=user, is_read=False
        ).exists()
        if not pending:
            Notification.objects.create(
                type=Notification.Type.MEMBER_CONVERSION_REQUEST,
                related_user=user,
                message=f"{user.get_full_name()} ({user.email}) pide pasar de cuenta portal a usuaria de la página.",
            )
        return Response({"detail": "Solicitud enviada. Un administrador la revisará."}, status=202)


# ---------------------------------------------------------------- Admin


class AdminBusinessOwnerViewSet(viewsets.ModelViewSet):
    """/api/admin/business-owners/ — asigna personas (dueña o vendedora) a un emprendimiento."""

    queryset = BusinessOwner.objects.all().select_related("user", "business")
    serializer_class = BusinessOwnerSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["business", "user", "role"]
    search_fields = ["user__email", "user__first_name", "user__last_name", "business__name"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def perform_create(self, serializer):
        access = serializer.save(assigned_by=self.request.user)
        log_activity(
            self.request.user, "portal_access_assigned",
            f"{self.request.user.email} asignó a {access.user.email} como {access.get_role_display().lower()} de «{access.business.name}».",
            target=access.business,
        )

    def perform_update(self, serializer):
        access = serializer.save()
        log_activity(
            self.request.user, "portal_access_updated",
            f"{self.request.user.email} cambió el rol de {access.user.email} en «{access.business.name}» a {access.get_role_display().lower()}.",
            target=access.business,
        )

    def perform_destroy(self, instance):
        log_activity(
            self.request.user, "portal_access_removed",
            f"{self.request.user.email} quitó a {instance.user.email} del portal de «{instance.business.name}».",
            target=instance.business,
        )
        instance.delete()


class AdminBenefitViewSet(viewsets.ReadOnlyModelViewSet):
    """/api/admin/benefits/ — revisión de beneficios antes de publicarse."""

    queryset = BusinessBenefit.objects.all().select_related("business").order_by("-updated_at")
    serializer_class = AdminBenefitSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["status", "business"]
    search_fields = ["business__name"]

    def _review(self, request, pk, new_status, verb):
        benefit = self.get_object()
        benefit.status = new_status
        benefit.reviewed_by = request.user
        benefit.reviewed_at = timezone.now()
        benefit.save()
        log_change(benefit.business, request.user, "benefit", "review", {"status": {"from": None, "to": new_status}})
        log_activity(
            request.user, f"benefit_{new_status}",
            f"{request.user.email} {verb} el beneficio de «{benefit.business.name}» ({benefit.percentage}%).",
            target=benefit.business,
        )
        return Response(self.get_serializer(benefit).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, pk, BusinessBenefit.Status.APPROVED, "aprobó")

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, pk, BusinessBenefit.Status.REJECTED, "rechazó")


class AdminMembershipViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """/api/admin/memberships/ — activar o suspender la membresía de las usuarias (por defecto, todas activas)."""

    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter(account_type="member", is_active=True, is_staff=False).select_related("membership")
    search_fields = ["email", "first_name", "last_name", "whatsapp"]
    ordering_fields = ["first_name", "created_at"]

    def get_serializer_class(self):
        class MembershipRowSerializer(serializers.ModelSerializer):
            membership_active = serializers.SerializerMethodField()
            has_document = serializers.SerializerMethodField()

            class Meta:
                model = User
                fields = ["id", "first_name", "last_name", "email", "whatsapp", "membership_active", "has_document"]

            def get_membership_active(self, obj):
                return has_active_membership(obj)

            def get_has_document(self, obj):
                return bool(obj.document_id)

        return MembershipRowSerializer

    @action(detail=True, methods=["patch"], url_path="set")
    def set_membership(self, request, pk=None):
        user = self.get_object()
        is_active = request.data.get("is_active")
        if not isinstance(is_active, bool):
            return Response({"is_active": ["Envía true o false."]}, status=400)
        Membership.objects.update_or_create(user=user, defaults={"is_active": is_active, "changed_by": request.user})
        verb = "activó" if is_active else "suspendió"
        log_activity(request.user, "membership_changed", f"{request.user.email} {verb} la membresía de {user.email}.", target=user)
        user.refresh_from_db()
        return Response(self.get_serializer(user).data)
