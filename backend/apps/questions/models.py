from django.conf import settings
from django.db import models

from apps.businesses.models import Business
from apps.core.models import TimeStampedModel


class Question(TimeStampedModel):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="questions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="questions")
    question = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} -> {self.business}: {self.question[:40]}"


class Answer(TimeStampedModel):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name="answer")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="answers")
    answer = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Respuesta a #{self.question_id}"
