from django.contrib.sitemaps.views import sitemap
from django.urls import path

from . import views
from .feeds import LatestPostsFeed
from .sitemaps import sitemaps

app_name = "blog"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("category/<slug:slug>/", views.CategoryView.as_view(), name="category"),
    path("tag/<slug:slug>/", views.TagView.as_view(), name="tag"),
    path("author/<slug:slug>/", views.AuthorView.as_view(), name="author"),
    path("feed/", LatestPostsFeed(), name="feed"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),  # must stay last
]