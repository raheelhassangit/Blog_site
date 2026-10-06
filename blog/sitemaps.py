from django.contrib.sitemaps import Sitemap
from django.db.models import Count, Q
from django.urls import reverse
from django.utils import timezone

from .models import AuthorProfile, Category, Post, Tag, Page
from .seo import MIN_POSTS_FOR_INDEXABLE_TAG


def published_filter(prefix="posts__"):
    return Q(**{f"{prefix}status": Post.Status.PUBLISHED, f"{prefix}published_at__lte": timezone.now()})


class StaticSitemap(Sitemap):
    changefreq, priority = "daily", 1.0

    def items(self):
        return ["blog:home"]

    def location(self, item):
        return reverse(item)


class PostSitemap(Sitemap):
    changefreq, priority = "weekly", 0.8

    def items(self):
        return Post.published.filter(noindex=False).order_by("-published_at")

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq, priority = "weekly", 0.6

    def items(self):
        return Category.objects.annotate(n=Count("posts", filter=published_filter())).filter(n__gt=0)


class TagSitemap(Sitemap):
    changefreq, priority = "weekly", 0.5

    def items(self):  # only tags with enough posts, matching the noindex rule in TagView
        return Tag.objects.annotate(n=Count("posts", filter=published_filter())).filter(
            n__gte=MIN_POSTS_FOR_INDEXABLE_TAG
        )


class AuthorSitemap(Sitemap):
    changefreq, priority = "monthly", 0.4

    def items(self):
        return AuthorProfile.objects.annotate(n=Count("posts", filter=published_filter())).filter(n__gt=0)

class PageSitemap(Sitemap):
    changefreq, priority = "yearly", 0.3

    def items(self):
        return Page.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

sitemaps = {
    "static": StaticSitemap, "posts": PostSitemap, "categories": CategorySitemap,
    "tags": TagSitemap, "authors": AuthorSitemap,
    "pages": PageSitemap,
}
