from django.conf import settings
from django.contrib.syndication.views import Feed

from .models import Post


class LatestPostsFeed(Feed):
    link = "/"

    def title(self):
        return settings.SITE_NAME

    def description(self):
        return settings.SITE_DESCRIPTION

    def items(self):
        return Post.published.select_related("author")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at

    def item_updateddate(self, item):
        return item.updated_at

    def item_author_name(self, item):
        return item.author.display_name