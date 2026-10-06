import re
from urllib.parse import urlparse

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()

_A_TAG = re.compile(r"<a\b([^>]*)>", re.I)
_HREF = re.compile(r'\shref="([^"]*)"', re.I)
_REL = re.compile(r'\srel="[^"]*"', re.I)
_TARGET = re.compile(r'\starget="[^"]*"', re.I)


def _is_affiliate(url):
    host = (urlparse(url.replace("&amp;", "&")).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in settings.AFFILIATE_DOMAINS)


@register.filter
def mark_links(html):
    """Tag links to known affiliate domains as sponsored. Input is already sanitized by nh3."""
    def fix(m):
        attrs = m.group(1)
        href = _HREF.search(attrs)
        if not href or not _is_affiliate(href.group(1)):
            return m.group(0)
        attrs = _TARGET.sub("", _REL.sub("", attrs))
        return f'<a{attrs} rel="sponsored nofollow noopener" target="_blank">'
    return mark_safe(_A_TAG.sub(fix, html))