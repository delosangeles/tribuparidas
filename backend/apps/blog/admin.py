from django.contrib import admin
from django.db.models import Count, Q

from .models import BlogCategory, BlogComment, BlogPost, BlogPostLike, BlogPostRead, BlogStage


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogStage)
class BlogStageAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "category", "status", "featured", "publication_date", "likes_total", "reads_total"]
    list_filter = ["status", "content_type", "category", "featured"]
    search_fields = ["title", "summary", "content"]
    autocomplete_fields = ["author", "category"]
    prepopulated_fields = {"slug": ("title",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _likes=Count("likes", distinct=True),
            _reads=Count("reads", filter=Q(reads__completed_at__isnull=False), distinct=True),
        )

    @admin.display(description="Me gusta", ordering="_likes")
    def likes_total(self, obj):
        return obj._likes

    @admin.display(description="Leídos", ordering="_reads")
    def reads_total(self, obj):
        return obj._reads


@admin.register(BlogPostLike)
class BlogPostLikeAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "created_at"]
    search_fields = ["post__title", "user__email"]
    autocomplete_fields = ["post", "user"]


@admin.register(BlogPostRead)
class BlogPostReadAdmin(admin.ModelAdmin):
    list_display = ["post", "user", "started_at", "completed_at"]
    list_filter = [("completed_at", admin.EmptyFieldListFilter)]
    search_fields = ["post__title", "user__email"]
    autocomplete_fields = ["post", "user"]


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "author__email", "post__title"]
    autocomplete_fields = ["author", "post"]
