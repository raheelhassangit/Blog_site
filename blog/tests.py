from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import AdSlot, AuthorProfile, Category, Post


class BlogSmokeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = AuthorProfile.objects.create(
            user=User.objects.create_user("t", password="x"), display_name="Tester")
        cls.cat = Category.objects.create(name="Summer")
        cls.live = Post.objects.create(
            title="Linen midi guide", excerpt="e", body="<p>hello linen</p>", category=cls.cat,
            author=cls.author, status="published", published_at=timezone.now())
        cls.draft = Post.objects.create(
            title="Secret draft", excerpt="e", body="<p>x</p>", category=cls.cat,
            author=cls.author, status="draft")

    def test_pages_load(self):
        for url in ["/", self.live.get_absolute_url(), self.cat.get_absolute_url(),
                    self.author.get_absolute_url(), "/sitemap.xml", "/robots.txt", "/feed/"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_draft_is_hidden_everywhere(self):
        self.assertEqual(self.client.get(self.draft.get_absolute_url()).status_code, 404)
        self.assertNotContains(self.client.get("/sitemap.xml"), self.draft.slug)
        self.assertNotContains(self.client.get("/"), "Secret draft")

    def test_search_finds_post(self):
        self.assertContains(self.client.get("/search/", {"q": "linen"}), "Linen midi guide")

    def test_scripts_are_stripped(self):
        p = Post.objects.create(title="X", excerpt="e", body="<p>ok</p><script>alert(1)</script>",
                                category=self.cat, author=self.author)
        self.assertNotIn("<script", p.body)

    def test_reserved_slug_is_avoided(self):
        p = Post.objects.create(title="Search", excerpt="e", body="<p>x</p>",
                                category=self.cat, author=self.author)
        self.assertEqual(p.slug, "search-post")

    def test_ads_only_render_when_active(self):
        url = self.live.get_absolute_url()
        self.assertNotContains(self.client.get(url), "Advertisement")
        ad = AdSlot.objects.create(name="a", placement="post_end", ad_code="<b>AD</b>")
        self.assertContains(self.client.get(url), "Advertisement")
        ad.is_active = False
        ad.save()
        self.assertNotContains(self.client.get(url), "Advertisement")