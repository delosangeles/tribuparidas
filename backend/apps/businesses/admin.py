from django.contrib import admin

from .models import Business, BusinessImage


class BusinessImageInline(admin.TabularInline):
    model = BusinessImage
    extra = 0


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "category", "city", "status", "average_rating", "created_at"]
    list_filter = ["status", "category", "department"]
    search_fields = ["name", "owner__email", "city"]
    inlines = [BusinessImageInline]
    readonly_fields = ["average_rating", "created_at", "updated_at"]
