# -*- coding: utf-8 -*-
"""
A "Try It" button beside Get Beta Access in the hero, with a glow around it.

The Try It page had no way in. It is a real page and it has been shared by link,
but nothing on the site pointed at it - the audit found it with no inbound links
at all, so the only visitors were people who already had the URL.

It sits in the hero rather than the nav, in the same fill as Get Beta Access, so
the two read as a pair of equal offers rather than a primary and a fallback.

The glow
--------
Short rays around an ellipse, pointing outward, pulsing. Drawn as one inline SVG
behind the button:

  aria-hidden and pointer-events:none  it is decoration, and it overhangs the
                                       button on every side, so without this it
                                       would swallow clicks meant for the button
  a fixed-size box, centred            the rays are laid out in their own
                                       coordinate space; stretching the SVG to
                                       the button's box would squash them on one
                                       axis as the label length changed
  alternating ray lengths              a ring of identical spokes reads as a
                                       loading spinner
  the pulse is opacity and scale       both are compositor-only, so this cannot
                                       cost layout on a page that already does
                                       scroll-driven work

The keyframes go in the page's own <style>, not in scroll-motion.js, so the glow
does not depend on that file having loaded.
"""
import glob
import io
import math
import os

BROWN = "#84512E"

HERO_CTA = ('<div onClick="{{ goAccess }}" style="padding:12px 28px;'
            'border-radius:10px;background:#84512E;color:#F9F9F7;'
            'font-size:.9375rem;font-weight:500;cursor:pointer">'
            'Get Beta Access</div>')

# The nav button this replaces.
NAV_BUTTON_PREFIX = '<a href="/try" style="margin-left:16px;padding:9px 17px;'


def _rays(count=28, cx=130, cy=62, rx=64, ry=33, short=9, long_=17):
    """Rays around an ellipse, alternating length, starting just off its edge."""
    out = []
    for i in range(count):
        a = (2 * math.pi * i) / count
        ux, uy = math.cos(a), math.sin(a)
        reach = long_ if i % 2 == 0 else short
        x1, y1 = cx + rx * ux, cy + ry * uy
        # step outward along the ellipse's own normal-ish direction
        x2, y2 = cx + (rx + reach) * ux, cy + (ry + reach) * uy
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f"/>' %
                   (x1, y1, x2, y2))
    return "".join(out)


# Built by concatenation, not %-formatting: the style string is full of literal
# percent signs (left:50%, scale) and every one of them would need escaping.
GLOW = (
    '<svg viewBox="0 0 260 124" aria-hidden="true" focusable="false" '
    'style="position:absolute;left:50%;top:50%;width:260px;height:124px;'
    'transform:translate(-50%,-50%);pointer-events:none;overflow:visible;'
    'stroke:' + BROWN + ';stroke-width:2;stroke-linecap:round;'
    'filter:drop-shadow(0 0 4px rgba(132,81,46,.55));'
    'animation:try-glow 2.6s ease-in-out infinite">' + _rays() + '</svg>'
)

# 26px of left margin on top of the row's own 12px gap. The rays reach about
# 35px past the button on every side, and without this they crossed the Get Beta
# Access button beside it - decoration drawn over a different control reads as a
# rendering fault, not as emphasis.
TRY_BUTTON = (
    '<div style="position:relative;display:inline-flex;margin-left:26px">'
    + GLOW +
    '<a href="/try" style="position:relative;padding:12px 28px;'
    'border-radius:10px;background:#84512E;color:#F9F9F7;font-size:.9375rem;'
    'font-weight:500;text-decoration:none;white-space:nowrap">Try It</a>'
    '</div>'
)

KEYFRAMES = (
    "\n  /* The hero Try It glow. opacity and scale only - both compositor-only,"
    "\n     so this cannot cost layout on a page already doing scroll work. */"
    "\n  @keyframes try-glow{0%,100%{opacity:.4;transform:translate(-50%,-50%) scale(1)}"
    "50%{opacity:1;transform:translate(-50%,-50%) scale(1.06)}}\n"
)


def apply(out):
    added = removed = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        before = s

        # take the nav button back out
        i = s.find(NAV_BUTTON_PREFIX)
        if i != -1:
            end = s.find("</a>", i) + len("</a>")
            s = s[:i] + s[end:]
            removed += 1

        if HERO_CTA in s and 'href="/try"' not in s:
            s = s.replace(HERO_CTA, HERO_CTA + TRY_BUTTON, 1)
            added += 1
            if "@keyframes try-glow" not in s:
                s = s.replace("\n</style>", KEYFRAMES + "</style>", 1)

        if s != before:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(s)

    print("  try button: added to %d hero(s), removed from %d nav(s)"
          % (added, removed))
    if added == 0:
        present = any('href="/try"' in io.open(p, encoding="utf-8", errors="surrogateescape").read()
                      for p in glob.glob(os.path.join(out, "*.html")))
        if not present:
            print("  hero CTA not found - no Try It button - CHECK")
