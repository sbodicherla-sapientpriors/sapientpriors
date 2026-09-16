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
Short rays around an ellipse, pointing outward, pulsing and turning slowly.

  the inner ellipse is SMALLER than  every ray starts behind the button and only
  the button                         the part clearing its edge is ever seen. At
                                     a wider radius the inner ends were all
                                     visible at once and drew the ellipse itself
                                     - a hard ring floating around the button,
                                     the one shape this effect must not have
  colour cycles per ray              within the brand's own family: the brown,
                                     and the golds and rusts either side of it,
                                     so it reads as light coming off the button
                                     rather than as confetti stuck to it
  it does not rotate                 a rotating ellipse sweeps a circle, and
                                     this one is wider than it is tall: turning
                                     it pushed the burst up into the sub-line
                                     and down into the logo row, and grew its
                                     box from 260x124 to 203x286. The ellipse
                                     stays aligned with the button it belongs to
  aria-hidden, pointer-events:none   it overhangs the button on every side, so
                                     without this it would swallow the clicks
                                     meant for the button
  a fixed box, centred, not stretched the rays live in their own coordinate
                                     space; sizing the SVG to the button would
                                     squash them on one axis when the label
                                     length changed
  alternating ray lengths            a ring of identical spokes reads as a
                                     loading spinner

Keyframes go in the page's own <style>, not in scroll-motion.js, so the glow
does not depend on that file having loaded.
"""
import glob
import io
import math
import os

HERO_CTA = ('<div onClick="{{ goAccess }}" style="padding:12px 28px;'
            'border-radius:10px;background:#84512E;color:#F9F9F7;'
            'font-size:.9375rem;font-weight:500;cursor:pointer">'
            'Get Beta Access</div>')

NAV_BUTTON_PREFIX = '<a href="/try" style="margin-left:16px;padding:9px 17px;'

RAY_COLOURS = ["#84512E", "#C2703A", "#E8A94E", "#D2643C", "#A8452A", "#E0B15F"]


def _rays(count=28, cx=130, cy=62, rx=40, ry=18, short=20, long_=29):
    out = []
    for i in range(count):
        a = (2 * math.pi * i) / count
        ux, uy = math.cos(a), math.sin(a)
        reach = long_ if i % 2 == 0 else short
        out.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s"/>' % (
                cx + rx * ux, cy + ry * uy,
                cx + (rx + reach) * ux, cy + (ry + reach) * uy,
                RAY_COLOURS[i % len(RAY_COLOURS)]))
    return "".join(out)


# Concatenated, not %-formatted: the style strings are full of literal percent
# signs and every one would need escaping.
GLOW = (
    '<span aria-hidden="true" style="position:absolute;left:50%;top:50%;'
    'width:260px;height:124px;margin-left:-130px;margin-top:-62px;'
    'pointer-events:none">'
    '<svg viewBox="0 0 260 124" focusable="false" '
    'style="width:100%;height:100%;overflow:visible;stroke-width:2.4;'
    'stroke-linecap:round;filter:drop-shadow(0 0 5px rgba(200,130,60,.45));'
    'animation:try-glow 2.6s ease-in-out infinite">' + _rays() + '</svg>'
    '</span>'
)

# 26px on top of the row's own 12px gap. The rays reach past the button on every
# side, and without it they crossed the Get Beta Access button beside it -
# decoration drawn over a different control reads as a rendering fault.
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
    "\n  @keyframes try-glow{0%,100%{opacity:.5;transform:scale(1)}"
    "50%{opacity:1;transform:scale(1.05)}}\n"
)


def apply(out):
    added = removed = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        before = s

        i = s.find(NAV_BUTTON_PREFIX)
        if i != -1:
            s = s[:i] + s[s.find("</a>", i) + 4:]
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
