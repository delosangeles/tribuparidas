from django.contrib import admin

from .models import ActivityLog, FeatureFlag


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "actor", "action", "description"]
    list_filter = ["action"]
    search_fields = ["description", "actor__email"]
    readonly_fields = ["actor", "action", "description", "content_type", "object_id", "created_at"]

    def has_add_permission(self, request):
        return False


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ["key", "label", "activate_at", "is_forced_active", "is_active", "updated_at"]
    list_filter = ["is_forced_active"]
    search_fields = ["key", "label"]
