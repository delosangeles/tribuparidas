from django.contrib import admin

from .models import Answer, Question


class AnswerInline(admin.StackedInline):
    model = Answer
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["business", "user", "question", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["question", "business__name", "user__email"]
    inlines = [AnswerInline]
