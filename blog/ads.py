import re

from django.core.cache import cache

from .models import AdSlot

_TOKEN = re.compile(r"<(/?)(?:blockquote|ul|ol|table|figure|pre)\b|</p>")


def active_ads():
    """{placement: AdSlot} for ads that are active and actually have content. Cached for 5 min."""
    ads = cache.get("active_ads")
    if ads is None:
        ads = {a.placement: a for a in AdSlot.objects.filter(is_active=True) if a.has_content}
        cache.set("active_ads", ads, 300)
    return ads


def split_body(html, after=3, minimum=6):
    """Split sanitized HTML after the Nth top-level paragraph (never inside quotes/lists/tables)."""
    depth = count = 0
    cut = None
    for m in _TOKEN.finditer(html):
        if m.group(0) == "</p>":
            if depth == 0:
                count += 1
                if count == after:
                    cut = m.end()
        else:
            depth += -1 if m.group(1) else 1
    if cut is None or count < minimum:
        return html, ""
    return html[:cut], html[cut:]