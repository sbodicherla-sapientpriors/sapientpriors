# -*- coding: utf-8 -*-
"""
The copyright line.

It read "© 2026 SapientPriors" - the current year alone, which says nothing
about how long the company has existed and quietly implies it started this year.
SapientPriors Inc. was incorporated in November 2025, so the notice runs from
there: "© 2025-2026".

The end year is taken from the build clock rather than typed in, because a
hardcoded year is wrong from the first of January and nobody notices until
somebody screenshots the footer. A build in 2027 will say 2025-2027 on its own,
and while the build still happens in 2025 it collapses to a single year rather
than printing a range with the same number on both sides.

This lives in its own module, and the string is matched loosely on the year, so
next January's build rewrites the line it finds rather than failing to match the
one it expected.
"""
import datetime
import glob
import io
import os
import re

FOUNDED = 2025

# "© 2026 SapientPriors" or "© 2025-2026 SapientPriors" - either is a target, so
# the patch is idempotent and survives its own previous output.
PATTERN = re.compile(r"©\s*\d{4}(?:\s*[-–]\s*\d{4})?\s+SapientPriors")


def apply(out, year=None):
    year = year or datetime.date.today().year
    span = str(FOUNDED) if year <= FOUNDED else "%d–%d" % (FOUNDED, year)
    want = "© %s SapientPriors" % span

    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        if not PATTERN.search(s):
            continue
        new = PATTERN.sub(want, s)
        if new != s:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(new)
            n += 1
    print("  copyright set to '%s' on %d file(s)" % (want, n))
    if n == 0 and not any(
            want in io.open(p, encoding="utf-8", errors="surrogateescape").read()
            for p in glob.glob(os.path.join(out, "*.html"))):
        print("  copyright line not found - CHECK")
