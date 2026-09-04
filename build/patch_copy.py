# -*- coding: utf-8 -*-
"""
Copy overrides. Edit this file to change wording anywhere on the site.

Why this exists
---------------
The site is built from a Claude Design export. Every .dc.html file in this repo
is generated, and re-exporting the design overwrites all of them - so wording
typed straight into a built page survives until the next export and then
silently reverts.

This file does not get overwritten. A pair here is re-applied on every build, so
a wording change made here is permanent. It is the only place a copy change
should be made unless you are already comfortable with the patch modules.

How to use it
-------------
Add a (find, replace) pair to COPY. The find text must match the page exactly,
including punctuation. Copy it out of the rendered page or out of the built
HTML rather than retyping it - the site uses typographic quotes and dashes
(' ' " " - -) that look identical to the ASCII ones in most editors and do not
compare equal.

    COPY = [
]

Then rebuild and check the output:

    python3 build/build.py <path to the design export>

Any pair that matches nothing prints a CHECK line naming it. A silent no-op is
the failure mode this file is designed to make impossible - do not ignore a
CHECK, it means your wording did not land and the old text is still live.

Where a pair applies
--------------------
Every generated .html file, which includes SiteNav.dc.html and
SiteFooter.dc.html - the nav and footer fragments every page fetches at runtime.
So a header or footer string only needs one pair.

What this cannot change
-----------------------
Anything built by JavaScript at runtime rather than written into the HTML: the
chart numbers, the counters in the stat tiles, the alumni strip's list, the
careers role list and the application form's questions. Those live in their
patch modules - see HANDOFF.md, "Where the copy lives".
"""
import glob
import io
import os

# (find, replace) - exact strings.
COPY = [
]


def apply(out):
    if not COPY:
        print("  copy: no overrides")
        return

    hits = {i: 0 for i in range(len(COPY))}
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        before = s
        for i, (old, new) in enumerate(COPY):
            if old in s:
                hits[i] += s.count(old)
                s = s.replace(old, new)
        if s != before:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(s)

    applied = sum(1 for i in hits if hits[i])
    print("  copy: %d of %d overrides applied" % (applied, len(COPY)))
    for i, (old, _) in enumerate(COPY):
        if not hits[i]:
            print("  copy override %d matched nothing: %r - CHECK" % (i + 1, old[:60]))
