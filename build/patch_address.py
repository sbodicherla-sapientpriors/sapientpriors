# -*- coding: utf-8 -*-
"""
The company address in the footer.

The export shipped a two-line US street address that came with the template and
was never ours. It is replaced with the address the company actually gives:
Chicago, Illinois.

One line, not two, so the block does not keep a second empty line where the
street used to be - removing content and leaving its spacing behind is a
recurring fault in this build.

Matched on the town rather than the whole block, so a change in the street line
above it does not make this silently match nothing.
"""
import glob
import io
import os

OLD_TOWN = "Sammamish, WA 98075"
NEW = "Chicago, Illinois"


def apply(out):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        if OLD_TOWN not in s:
            continue
        i = s.index(OLD_TOWN)
        # the two <span style="display:block"> lines: street, then town
        town_open = s.rindex("<span", 0, i)
        street_open = s.rindex("<span", 0, town_open)
        town_close = s.index("</span>", i) + len("</span>")
        s = (s[:street_open]
             + '<span style="display:block">%s</span>' % NEW
             + s[town_close:])
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  address set to '%s' on %d file(s)" % (NEW, n))
    if n == 0:
        found = any(NEW in io.open(p, encoding="utf-8", errors="surrogateescape").read()
                    for p in glob.glob(os.path.join(out, "*.html")))
        if not found:
            print("  address block not found - CHECK")
