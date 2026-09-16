# -*- coding: utf-8 -*-
"""
A "Try It" button beside the beta CTA in the nav.

The Try It page had no way in. It is a real page, it has been shared by link,
and nothing on the site pointed at it - the audit found it with no inbound links
at all, so the only visitors were people who already had the URL.

Secondary styling, not a second filled button: two solid brown buttons side by
side compete, and the beta CTA is the one that should win. Same height, radius
and padding as the primary so they read as a pair, with a hairline border and
ink text instead of a fill.

Placed before the primary, because the rightmost button is the one a reader
treats as the main action and that is still Get Beta Access.
"""
import glob
import io
import os

PRIMARY = ('<a href="/#access" style="margin-left:16px;padding:10px 18px;'
           'border-radius:10px;background:#84512E;color:#F9F9F7;font-size:.875rem;'
           'font-weight:500;text-decoration:none">Get Beta Access</a>')

# 9px of padding, not 10: the 1px border adds 2px to the box the filled button
# does not have, and at 10px this rendered 39px tall beside a 37px primary. Two
# buttons side by side at different heights is the kind of thing nobody names
# but everybody sees.
SECONDARY = ('<a href="/try" style="margin-left:16px;padding:9px 17px;'
             'border-radius:10px;border:1px solid #CFCFC9;color:#14161A;'
             'font-size:.875rem;font-weight:500;text-decoration:none" '
             'style-hover="background:#F6F6F4">Try It</a>')


def apply(out):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        if PRIMARY not in s or 'href="/try"' in s:
            continue
        s = s.replace(PRIMARY, SECONDARY + PRIMARY, 1)
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  try button added to %d file(s)" % n)
    if n == 0:
        already = any('href="/try"' in io.open(p, encoding="utf-8", errors="surrogateescape").read()
                      for p in glob.glob(os.path.join(out, "*.html")))
        if not already:
            print("  nav CTA not found - no Try It button - CHECK")
