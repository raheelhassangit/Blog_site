from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from .models import Category, Page
from .sitemaps import published_filter


def site(request):
    cats = cache.get("nav_categories")
    pages = cache.get("footer_pages")
    if pages is None:
        pages = list(Page.objects.filter(show_in_footer=True))
        cache.set("footer_pages", pages, 300)
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DESCRIPTION": settings.SITE_DESCRIPTION,
        "nav_categories": cats,
        "footer_pages": pages,
    }