from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminQuestionViewSet, AnswerCreateView, BusinessQuestionsView, MyQuestionsListView

admin_router = DefaultRouter()
admin_router.register("admin/questions", AdminQuestionViewSet, basename="admin-question")

urlpatterns = [
    path("businesses/<int:business_id>/questions/", BusinessQuestionsView.as_view(), name="business-questions"),
    path("my/questions/", MyQuestionsListView.as_view(), name="my-questions"),
    path("questions/<int:id>/answer/", AnswerCreateView.as_view(), name="question-answer"),
    *admin_router.urls,
]
