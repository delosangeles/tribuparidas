from django.contrib import admin

from .models import BlogCategory, BlogComment, BlogPost, BlogStage


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
    list_display = ["title", "author", "category", "status", "featured", "publication_date"]
    list_filter = ["status", "content_type", "category", "featured"]
    search_fields = ["title", "summary", "content"]
    autocomplete_fields = ["author", "category"]
    prepopulated_fields = {"slug": ("title",)}


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["content", "author__email", "post__title"]
    autocomplete_fields = ["author", "post"]
