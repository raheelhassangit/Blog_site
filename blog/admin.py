from django.contrib import admin
from .models import AuthorProfile, Category, Post, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AuthorProfile)
class AuthorProfileAdmin(admin.ModelAdmin):
    list_display = ("display_name", "user")
    prepopulated_fields = {"slug": ("display_name",)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "published_at")
    list_filter = ("status", "category", "author")
    search_fields = ("title", "excerpt")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("tags",)
    date_hierarchy = "published_at"
    fieldsets = (
        (None, {"fields": ("title", "slug", "excerpt", "body")}),
        ("Media", {"fields": ("cover_image", "cover_alt")}),
        ("Organization", {"fields": ("category", "tags", "author")}),
        ("Publishing", {"fields": ("status", "published_at")}),
        ("SEO (optional overrides)", {"classes": ("collapse",),
                                      "fields": ("meta_title", "meta_description", "noindex")}),
    )