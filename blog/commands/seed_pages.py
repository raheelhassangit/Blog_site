from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand

from blog.models import Page


class Command(BaseCommand):
    help = "Create starter About, Contact, Privacy Policy and Affiliate Disclosure pages (never overwrites)."

    def handle(self, *args, **options):
        n, mail = settings.SITE_NAME, settings.CONTACT_EMAIL
        today = date.today().strftime("%B %d, %Y")

        pages = {
            "about": ("About", f"About {n}: a women's dress journal with guides on fit, fabric and styling.", f"""
<p>{n} is a women's dress journal. We write practical guides on fit, fabric and styling, so you can find the right dress for the occasion and feel good wearing it.</p>
<h2>What you'll find here</h2>
<ul><li>Occasion guides, from weddings and parties to workdays and everyday wear</li>
<li>Honest notes on cut, length and fabric</li>
<li>Seasonal style ideas and what to look for when you shop</li></ul>
<h2>How this site is funded</h2>
<p>{n} is supported by advertising and affiliate links. Our opinions are our own, and we only recommend things we would genuinely suggest to a friend. Read more in our <a href="/affiliate-disclosure/">affiliate disclosure</a>.</p>
<p>Questions or ideas? <a href="/contact/">Get in touch</a>.</p>"""),

            "contact": ("Contact", f"Contact {n} for questions, collaborations or corrections.", f"""
<p>We'd love to hear from you, whether it's a question, a correction or a collaboration idea.</p>
<p>Email: <a href="mailto:{mail}">{mail}</a></p>
<p>We aim to reply within a few business days. For brand collaborations, please include a short description of the product or idea.</p>"""),

            "privacy-policy": ("Privacy Policy", f"How {n} handles visitor information, cookies, advertising and affiliate links.", f"""
<p>This policy explains what information {n} (the "site") collects and how it is used. Last updated: {today}.</p>
<h2>Information we collect</h2>
<p>You don't need an account to read the site. Our hosting provider records technical information such as IP address, browser type and the pages requested in server logs, for security and to keep the site running. If you email us, we keep your message and address so we can reply.</p>
<h2>Cookies and local storage</h2>
<p>We store your light or dark mode choice in your browser's local storage on your own device. Third parties that serve ads or track affiliate purchases (see below) may set their own cookies.</p>
<h2>Advertising</h2>
<p>We use third-party advertising services, including Google AdSense. These vendors use cookies to show ads based on your visits to this and other websites. You can manage personalised advertising in <a href="https://adssettings.google.com">Google Ads Settings</a> or opt out of many vendors at <a href="https://www.aboutads.info">aboutads.info</a>.</p>
<h2>Affiliate links</h2>
<p>Some links on this site are affiliate links. If you click one and buy something, we may earn a commission at no extra cost to you. The retailer or affiliate network may use cookies to record the referral. See our <a href="/affiliate-disclosure/">affiliate disclosure</a>.</p>
<h2>Third-party sites</h2>
<p>We link to other websites. We are not responsible for their content or privacy practices.</p>
<h2>Children</h2>
<p>This site is not directed at children under 13, and we do not knowingly collect their information.</p>
<h2>Changes and contact</h2>
<p>We may update this policy from time to time and will change the date above when we do. Questions: <a href="mailto:{mail}">{mail}</a>.</p>"""),

            "affiliate-disclosure": ("Affiliate Disclosure", f"How {n} earns commissions from affiliate links.", f"""
<p>{n} participates in affiliate programs. This means some links on the site are affiliate links: if you click one and make a purchase, we may earn a small commission at no extra cost to you.</p>
<h2>Our promise</h2>
<ul><li>Commissions never decide what we write about or how we rate it.</li>
<li>Posts that contain affiliate links say so at the top.</li>
<li>Affiliate links are tagged as sponsored so search engines and readers can tell.</li></ul>
<p>Questions about this disclosure? Email <a href="mailto:{mail}">{mail}</a>.</p>"""),
        }

        for slug, (title, desc, body) in pages.items():
            _, created = Page.objects.get_or_create(
                slug=slug, defaults={"title": title, "meta_description": desc[:160], "body": body.strip()}
            )
            self.stdout.write(f"{'Created' if created else 'Kept existing'}: {title}")