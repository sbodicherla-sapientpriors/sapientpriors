"""
Keep the internal review build out of every search index.

The site is shared by link with the team while it is still being written, and
a page with two empty benchmark rows and four placeholder legal pages is not
one you want turning up in a search for the company. There is no password:
the ask was link-only, not gated.

Three layers, because each one covers a hole the others leave:

  robots.txt          asks crawlers not to fetch anything. A page that is
                      never fetched is also never indexed - but a URL that is
                      linked from somewhere else can still be indexed *without*
                      being fetched, showing as a bare title with no snippet.
  <meta name=robots>  this file. Covers that case, because it is the page
                      itself saying "do not index me". Only works on documents
                      a crawler parses as HTML.
  X-Robots-Tag        set in vercel.json. Same instruction at the HTTP layer,
                      so it also covers the PDF, data/manual.json and the API
                      routes, which have no <head> to put a meta tag in.

None of this is access control, and it should not be described to anyone as
such. It stops the site being *found*; it does not stop it being *opened*.
Anyone holding the link can read everything. Vercel's Hobby plan has no
deployment protection, so a real gate would mean a paid plan or a password,
and a password was explicitly ruled out.

Delete this module, robots.txt and the X-Robots-Tag block on launch day.
"""

import glob
import os

TAG = ('<meta name="robots" '
       'content="noindex, nofollow, noarchive, nosnippet, noimageindex">')

ANCHOR = '<meta name="viewport" content="width=device-width, initial-scale=1">'


def apply(out):
    touched = 0
    for p in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        if 'name="robots"' in s:
            continue
        if ANCHOR not in s:
            print("  %-28s no viewport meta to anchor to - CHECK"
                  % os.path.basename(p))
            continue
        s = s.replace(ANCHOR, ANCHOR + "\n" + TAG, 1)
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        touched += 1
    print("  noindex meta added to %d pages" % touched)
