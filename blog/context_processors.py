from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

from .models import Category
from .sitemaps import published_filter


def site(request):
    cats = cache.get("nav_categories")
    if cats is None:
        cats = list(
            Category.objects.annotate(post_count=Count("posts", filter=published_filter()))
            .filter(post_count__gt=0)
        )
        cache.set("nav_categories", cats, 300)
    return {"SITE_NAME": settings.SITE_NAME, "nav_categories": cats}