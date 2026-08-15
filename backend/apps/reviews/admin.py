from django.contrib import admin

from .models import Favorite, Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["business", "user", "rating", "is_active", "created_at"]
    list_filter = ["rating", "is_active"]
    search_fields = ["business__name", "user__email", "comment"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "business", "created_at"]
    search_fields = ["business__name", "user__email"]
