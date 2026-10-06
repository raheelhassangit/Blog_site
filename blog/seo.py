import json

from django.conf import settings

MIN_POSTS_FOR_INDEXABLE_TAG = 3  # thin tag pages hurt rankings, so they stay noindex until they have content


def ld_json(data):
    """Serialize for <script type="application/ld+json"> without allowing a </script> breakout."""
    return json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")


class SEOMixin:
    def build_seo(self, *, title, description="", og_type="website", image="",
                  noindex=False, json_ld=None, full_title=None):
        request = self.request
        canonical = request.build_absolute_uri(request.path)
        page = request.GET.get("page", "")
        if page.isdigit() and int(page) > 1:
            canonical += f"?page={int(page)}"
        if image and image.startswith("/"):
            image = request.build_absolute_uri(image)
        return {
            "title": full_title or f"{title} | {settings.SITE_NAME}",
            "description": description[:160],
            "canonical": canonical,
            "og_type": og_type,
            "image": image,
            "noindex": noindex,
            "json_ld": ld_json(json_ld) if json_ld else "",
        }