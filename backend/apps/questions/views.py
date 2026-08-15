from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.businesses.models import Business

from .models import Answer, Question
from .serializers import AnswerCreateSerializer, AnswerSerializer, QuestionCreateSerializer, QuestionSerializer


class BusinessQuestionsView(generics.ListCreateAPIView):
    """GET público /api/businesses/{business_id}/questions/, POST requiere sesión."""

    ordering_fields = ["created_at"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuestionCreateSerializer
        return QuestionSerializer

    def get_business(self):
        return get_object_or_404(
            Business, pk=self.kwargs["business_id"], status=Business.Status.APPROVED
        )

    def get_queryset(self):
        return Question.objects.filter(business=self.get_business(), is_active=True)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save(business=self.get_business(), user=self.request.user)
        output = QuestionSerializer(question).data
        return Response(output, status=201)


class MyQuestionsListView(generics.ListAPIView):
    """GET /api/my/questions/ — preguntas recibidas en todos los negocios del usuario."""

    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["business"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        return Question.objects.filter(business__owner=self.request.user).select_related("business", "user", "answer")


class AnswerCreateView(APIView):
    """POST /api/questions/{id}/answer/ — solo el dueño del negocio puede responder."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        question = get_object_or_404(Question, pk=id)
        if question.business.owner_id != request.user.id:
            return Response({"detail": "No tienes permiso para responder esta pregunta."}, status=403)

        serializer = AnswerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answer, _created = Answer.objects.update_or_create(
            question=question,
            defaults={"answer": serializer.validated_data["answer"], "user": request.user},
        )
        return Response(AnswerSerializer(answer).data, status=201)


class AdminQuestionViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):
    """/api/admin/questions/ — moderación: ocultar/reactivar preguntas."""

    queryset = Question.objects.all().select_related("business", "user", "answer")
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ["is_active", "business"]
    search_fields = ["question", "business__name", "user__email"]
    ordering_fields = ["created_at"]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        return Response(status=204)
