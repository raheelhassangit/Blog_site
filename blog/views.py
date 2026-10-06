from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_safe
from django.views.generic import DetailView, ListView, TemplateView
from .sitemaps import published_filter

from .models import AuthorProfile, Category, Post, Tag
from .seo import MIN_POSTS_FOR_INDEXABLE_TAG, SEOMixin
from .seo import ld_json

PAGE_SIZE = 12


def listing_qs():
    return Post.published.select_related("category", "author").prefetch_related("tags")


class HomeView(SEOMixin, TemplateView):
    template_name = "blog/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        latest = list(listing_qs()[:7])
        ctx["featured"] = latest[0] if latest else None
        ctx["latest"] = latest[1:7]
        ctx["tags"] = (
            Tag.objects.annotate(n=Count("posts", filter=published_filter()))
            .filter(n__gt=0).order_by("-n", "name")[:14]
        )
        top = (
            Category.objects.annotate(n=Count("posts", filter=published_filter()))
            .filter(n__gt=0).order_by("-n")[:3]
        )
        ctx["sections"] = [(c, list(listing_qs().filter(category=c)[:3])) for c in top]
        ctx["seo"] = self.build_seo(
            title=settings.SITE_NAME,
            full_title=f"{settings.SITE_NAME} | Women's Dress Ideas & Style Guides",
            description=settings.SITE_DESCRIPTION,
        )
        return ctx


class PostDetailView(SEOMixin, DetailView):
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        # Staff can preview drafts and scheduled posts; everyone else only sees published ones.
        base = Post.objects if self.request.user.is_staff else Post.published
        return base.select_related("category", "author").prefetch_related("tags")

    def get_related(self, post):
        related = list(
            Post.published.filter(tags__in=post.tags.all()).exclude(pk=post.pk)
            .annotate(shared=Count("tags")).order_by("-shared", "-published_at")
            .select_related("category")[:3]
        )
        if len(related) < 3:
            seen = [p.pk for p in related] + [post.pk]
            related += list(
                Post.published.filter(category=post.category).exclude(pk__in=seen)
                .select_related("category")[: 3 - len(related)]
            )
        return related

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        post = self.object
        now = timezone.now()
        ctx["is_preview"] = not (
            post.status == Post.Status.PUBLISHED and post.published_at and post.published_at <= now
        )
        ctx["related_posts"] = self.get_related(post)

        image = post.cover_image.url if post.cover_image else ""
        seo = self.build_seo(
            title=post.meta_title or post.title,
            description=post.meta_description or post.excerpt,
            og_type="article", image=image,
            noindex=post.noindex or ctx["is_preview"],
        )
        absolute = self.request.build_absolute_uri
        article = {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post.title[:110],
            "description": seo["description"],
            "datePublished": post.published_at.isoformat() if post.published_at else None,
            "dateModified": post.updated_at.isoformat(),
            "author": {"@type": "Person", "name": post.author.display_name,
                       "url": absolute(post.author.get_absolute_url())},
            "publisher": {"@type": "Organization", "name": settings.SITE_NAME},
            "mainEntityOfPage": seo["canonical"],
            "image": [seo["image"]] if seo["image"] else None,
            "keywords": ", ".join(t.name for t in post.tags.all()),
            "articleSection": post.category.name,
        }
        article = {k: v for k, v in article.items() if v}
        breadcrumbs = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": absolute("/")},
                {"@type": "ListItem", "position": 2, "name": post.category.name,
                 "item": absolute(post.category.get_absolute_url())},
                {"@type": "ListItem", "position": 3, "name": post.title},
            ],
        }
        seo["json_ld"] = ld_json([article, breadcrumbs])
        ctx["seo"] = seo
        return ctx

    def render_to_response(self, context, **kwargs):
        response = super().render_to_response(context, **kwargs)
        if context["is_preview"]:
            response["X-Robots-Tag"] = "noindex"
            response["Cache-Control"] = "private, no-store"
        return response


class CategoryView(SEOMixin, ListView):
    template_name = "blog/category.html"
    context_object_name = "posts"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs["slug"])
        return listing_qs().filter(category=self.category)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c = self.category
        ctx["category"] = c
        ctx["seo"] = self.build_seo(
            title=c.name,
            description=c.meta_description or c.intro or f"Posts about {c.name}.",
        )
        return ctx


class TagView(SEOMixin, ListView):
    template_name = "blog/tag.html"
    context_object_name = "posts"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return listing_qs().filter(tags=self.tag)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        total = ctx["page_obj"].paginator.count if ctx.get("page_obj") else 0
        ctx["tag"] = self.tag
        ctx["seo"] = self.build_seo(
            title=f"{self.tag.name} articles",
            description=f"All posts tagged {self.tag.name}.",
            noindex=total < MIN_POSTS_FOR_INDEXABLE_TAG,
        )
        return ctx


class AuthorView(SEOMixin, ListView):
    template_name = "blog/author.html"
    context_object_name = "posts"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.author = get_object_or_404(AuthorProfile, slug=self.kwargs["slug"])
        return listing_qs().filter(author=self.author)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["author"] = self.author
        ctx["seo"] = self.build_seo(
            title=f"Posts by {self.author.display_name}",
            description=self.author.bio or f"Articles written by {self.author.display_name}.",
            og_type="profile",
        )
        return ctx


class SearchView(SEOMixin, ListView):
    template_name = "blog/search.html"
    context_object_name = "posts"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        self.query = self.request.GET.get("q", "").strip()[:100]
        if not self.query:
            return Post.published.none()
        # "websearch" never raises on odd input and supports "quoted phrases", or, and -exclusions.
        sq = SearchQuery(self.query, config="english", search_type="websearch")
        return (
            listing_qs().filter(search_vector=sq)
            .annotate(rank=SearchRank("search_vector", sq))
            .order_by("-rank", "-published_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.query
        ctx["seo"] = self.build_seo(
            title=f'Search results for "{self.query}"' if self.query else "Search",
            noindex=True,
        )
        return ctx


@require_safe
def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /search/",
        "",
        f"Sitemap: {request.build_absolute_uri(reverse('blog:sitemap'))}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")