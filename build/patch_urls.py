# -*- coding: utf-8 -*-
"""
Stop the site advertising its own .dc.html URLs.

The clean paths shipped as rewrites with 308s behind them, and Google and
HubSpot both still list /Careers.dc.html. A redirect does not undo being linked:
every href in the markup, and the HOME constant the nav and footer build their
links from, still named the old file. A crawler follows those, is redirected,
and keeps the original as the address it discovered.

Three things fix it, and all three are needed:

  1. The links. Nothing on the site should point at a .dc.html page any more,
     so there is nothing left to discover under the old address.
  2. rel=canonical on every page, naming the clean URL. This is the part that
     tells a crawler which of two addresses to keep when it already has both.
  3. A sitemap listing only the clean set, so the canonical list is stated
     rather than inferred.

Fragments are left alone as fetch targets - SiteNav and SiteFooter are pulled in
at runtime by every page and must keep resolving - but the hrefs written inside
them are rewritten like any others.
"""
import datetime
import glob
import io
import os

SITE = "https://www.sapientpriors.com"

# file on disk -> the address it should be known by
CLEAN = {
    "index.html": "/",
    "SapientPriors.dc.html": "/",
    "API Docs.dc.html": "/docs",
    "Careers.dc.html": "/careers",
    "Team.dc.html": "/team",
    "TryIt.dc.html": "/try",
    "Research.dc.html": "/research",
    "Pricing.dc.html": "/pricing",
}

# Only what should be found. Research and Pricing carry a noindex while they say
# they are still being built, so listing them would contradict that header.
SITEMAP = ["/", "/docs", "/careers", "/team", "/try"]

# Longest first: "SapientPriors.dc.html#access" must be rewritten before the
# bare "SapientPriors.dc.html" inside it.
LINKS = [
    ("SapientPriors.dc.html#access", "/#access"),
    ("SapientPriors.dc.html#demo", "/#demo"),
    ("API%20Docs.dc.html", "/docs"),
    ("API Docs.dc.html", "/docs"),
    ("SapientPriors.dc.html", "/"),
    ("Careers.dc.html", "/careers"),
    ("Team.dc.html", "/team"),
    ("TryIt.dc.html", "/try"),
    ("Research.dc.html", "/research"),
    ("Pricing.dc.html", "/pricing"),
]

# The nav and footer build hrefs from this rather than writing them out.
HOME_FROM = "const HOME = 'SapientPriors.dc.html';"
HOME_TO = "const HOME = '/';"

# The runtime fetches these by filename; rewriting the fetch itself would take
# the nav and footer off every page.
KEEP_FETCHABLE = ("SiteNav.dc.html", "SiteFooter.dc.html")


def apply(out):
    rewritten = canon = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        name = os.path.basename(path)
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        before = s

        s = s.replace(HOME_FROM, HOME_TO)
        for old, new in LINKS:
            # only inside href="..." and href='...', so a fetch of
            # SiteNav.dc.html or a title mentioning a page is untouched
            s = s.replace('href="%s"' % old, 'href="%s"' % new)
            s = s.replace("href='%s'" % old, "href='%s'" % new)
            s = s.replace("href: '%s'" % old, "href: '%s'" % new)

        clean = CLEAN.get(name)
        if clean and 'rel="canonical"' not in s and "<head>" in s:
            tag = '<link rel="canonical" href="%s%s">' % (SITE, clean)
            s = s.replace("<head>", "<head>\n" + tag, 1)
            canon += 1

        if s != before:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(s)
            rewritten += 1

    left = 0
    for path in glob.glob(os.path.join(out, "*.html")):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        for tpl in ('href="%s', "href='%s"):
            for f in CLEAN:
                if (tpl % f) in s or (tpl % f.replace(" ", "%20")) in s:
                    left += 1

    today = datetime.date.today().isoformat()
    urls = "".join(
        "\n  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, today)
        for u in SITEMAP)
    io.open(os.path.join(out, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s\n'
        '</urlset>\n' % urls)

    print("  urls: %d files rewritten, %d canonicals, sitemap with %d entries"
          % (rewritten, canon, len(SITEMAP)))
    if left:
        print("  %d .dc.html hrefs still in the markup - CHECK" % left)
