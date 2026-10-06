import math

import nh3
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.conf import settings
from django.db import models
from django.db.models import Value
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.core.exceptions import ValidationError

RESERVED_SLUGS = {
    "admin", "search", "category", "tag", "author", "feed", "sitemap",
    "robots", "static", "media", "ckeditor5", "about", "contact", "privacy", "terms",
    "privacy-policy", "affiliate-disclosure",
}

# Whitelist for editor HTML. Anything not listed is stripped on save.
ALLOWED_TAGS = {
    "p", "br", "h2", "h3", "h4", "strong", "em", "u", "s", "blockquote",
    "ul", "ol", "li", "a", "img", "figure", "figcaption", "pre", "code",
    "table", "thead", "tbody", "tr", "th", "td", "hr",
}
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "width", "height"},
    "code": {"class"},   # language-xxx for code highlighting
    "pre": {"class"},
}


def unique_slug(instance, source, max_length=200):
    base = slugify(source)[:max_length] or "post"
    slug, n = base, 2
    Model = instance.__class__
    while Model.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
        slug = f"{base[:max_length - 4]}-{n}"
        n += 1
    return slug

ALLOWED_ATTRS = {
    "a": {"href", "title", "rel", "target"},   # rel/target now allowed
    "img": {"src", "alt", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
}


def clean_html(html):
    return nh3.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                     url_schemes={"http", "https", "mailto"}, link_rel=None)

class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    intro = models.TextField(blank=True, help_text="Shown at the top of the category page (good for SEO).")
    meta_description = models.CharField(max_length=160, blank=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 90)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:category", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=70, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.name, 70)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:tag", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


class AuthorProfile(models.Model):
    """Public author info. Login still uses Django's built-in User (admin only)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="author_profile")
    display_name = models.CharField(max_length=80)
    slug = models.SlugField(max_length=90, unique=True, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="authors/", blank=True)
    website = models.URLField(blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.display_name, 90)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:author", kwargs={"slug": self.slug})

    def __str__(self):
        return self.display_name


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset()
            .filter(status=Post.Status.PUBLISHED, published_at__lte=timezone.now())
        )


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    excerpt = models.CharField(max_length=300, help_text="Short summary for cards and as the fallback meta description.")
    body = CKEditor5Field("Body", config_name="default")

    cover_image = models.ImageField(upload_to="covers/%Y/%m/", blank=True)
    cover_alt = models.CharField(max_length=200, blank=True, help_text="Describe the image (accessibility + image SEO).")

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="posts")
    tags = models.ManyToManyField(Tag, blank=True, related_name="posts")
    author = models.ForeignKey(AuthorProfile, on_delete=models.PROTECT, related_name="posts")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True, help_text="Set a future date to schedule.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO overrides
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.CharField(max_length=160, blank=True)
    noindex = models.BooleanField(default=False)

    reading_time = models.PositiveSmallIntegerField(default=1, editable=False)
    search_vector = SearchVectorField(null=True, editable=False)

    objects = models.Manager()
    published = PublishedManager()

    def clean(self):
        super().clean()
        if self.slug in RESERVED_SLUGS:
            raise ValidationError({"slug": "This slug is reserved for a site page."})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
            if self.slug in RESERVED_SLUGS:
                self.slug = f"{self.slug}-post"
        # ... rest of your existing save() unchanged
    
    has_affiliate_links = models.BooleanField(
        default=False, help_text="Shows an affiliate disclosure at the top of this post."
    )
        
    class Meta:
        ordering = ["-published_at"]
        indexes = [
            GinIndex(fields=["search_vector"], name="post_search_gin"),
            models.Index(fields=["status", "-published_at"], name="post_status_pub_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slug(self, self.title)
        # Sanitize editor HTML before it ever hits the DB.
        self.body = nh3.clean(self.body, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS,
                              url_schemes={"http", "https", "mailto"})
        words = len(nh3.clean(self.body, tags=set()).split())
        self.reading_time = max(1, math.ceil(words / 200))
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def update_search_vector(self):
        """Weighted: title+tags (A) > excerpt (B) > body (C). Called from signals."""
        text = nh3.clean(self.body, tags=set())
        tags = " ".join(self.tags.values_list("name", flat=True))
        vector = (
            SearchVector(Value(self.title), weight="A", config="english")
            + SearchVector(Value(tags), weight="A", config="english")
            + SearchVector(Value(self.excerpt), weight="B", config="english")
            + SearchVector(Value(text), weight="C", config="english")
        )
        Post.objects.filter(pk=self.pk).update(search_vector=vector)

    def get_absolute_url(self):
        return reverse("blog:post_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title
    
class AdSlot(models.Model):
    class Placement(models.TextChoices):
        POST_TOP = "post_top", "Post page: above the article text"
        POST_MIDDLE = "post_middle", "Post page: middle of the article"
        POST_END = "post_end", "Post page: after the article"

    name = models.CharField(max_length=80, help_text="Only for you, e.g. 'AdSense top' or 'Amazon summer dress banner'.")
    placement = models.CharField(max_length=20, choices=Placement.choices, unique=True)
    is_active = models.BooleanField(default=True, help_text="Untick to hide this ad without deleting it.")
    ad_code = models.TextField("Ad network code", blank=True, help_text="Paste the full snippet from AdSense or another network.")
    banner = models.ImageField(upload_to="ads/", blank=True)
    banner_alt = models.CharField(max_length=150, blank=True)
    link_url = models.URLField("Affiliate link", blank=True, help_text="Where the banner points to.")

    class Meta:
        ordering = ["placement"]

    @property
    def has_content(self):
        return bool(self.ad_code.strip() or (self.banner and self.link_url))

    def clean(self):
        if self.ad_code.strip() and self.banner:
            raise ValidationError("Use either ad code or a banner, not both.")
        if not self.has_content:
            raise ValidationError("Add ad code, or a banner image together with its link.")

    def __str__(self):
        return f"{self.name} ({self.get_placement_display()})"    
    
PAGE_SLUGS = [
    ("about", "About"),
    ("contact", "Contact"),
    ("privacy-policy", "Privacy Policy"),
    ("affiliate-disclosure", "Affiliate Disclosure"),
]


class Page(models.Model):
    slug = models.SlugField(max_length=40, choices=PAGE_SLUGS, unique=True)
    title = models.CharField(max_length=120)
    body = CKEditor5Field("Body", config_name="default")
    meta_description = models.CharField(max_length=160, blank=True)
    show_in_footer = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def save(self, *args, **kwargs):
        self.body = clean_html(self.body)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("blog:page", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title    