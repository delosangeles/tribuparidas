from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Notification, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["-created_at"]
    list_display = ["email", "first_name", "last_name", "whatsapp", "is_staff", "is_active", "created_at"]
    list_filter = ["is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name", "whatsapp"]
    readonly_fields = ["created_at", "updated_at", "last_login"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("first_name", "last_name", "whatsapp")}),
        ("Permisos", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Fechas", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name", "whatsapp", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["type", "message", "related_user", "is_read", "created_at"]
    list_filter = ["type", "is_read"]
    search_fields = ["message", "related_user__email"]
