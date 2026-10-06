from django.contrib import admin
from .models import AuthorProfile, Category, Post, Tag
from .models import AdSlot  
from .models import Page

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
        ("Publishing", {"fields": ("status", "published_at", "has_affiliate_links")}),
        ("SEO (optional overrides)", {"classes": ("collapse",),
                                      "fields": ("meta_title", "meta_description", "noindex")}),
    )

@admin.register(AdSlot)
class AdSlotAdmin(admin.ModelAdmin):
    list_display = ("name", "placement", "kind", "is_active")
    list_editable = ("is_active",)
    fieldsets = (
        (None, {"fields": ("name", "placement", "is_active")}),
        ("Option A: ad network code (AdSense etc.)", {"fields": ("ad_code",)}),
        ("Option B: affiliate banner", {"fields": ("banner", "banner_alt", "link_url")}),
    )

    @admin.display(description="Type")
    def kind(self, obj):
        return "Code" if obj.ad_code.strip() else "Banner" if obj.banner else "Empty"        
    
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "show_in_footer", "updated_at")     