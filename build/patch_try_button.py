# -*- coding: utf-8 -*-
"""
A "Try It" button beside Get Beta Access in the hero, with a glow around it.

Points at /#playground - the demo now lives on the home page, straight after
"What changes", rather than on a page of its own. Not /try, which is the pitch
page that asks you to book a session: a button labelled "Try It" beside "Get
Beta Access" promises the thing you can use now, and /try is the same kind of
ask as the button next to it.

A plain hash link, so clicking it is a scroll and nothing else - no transition,
no entrance animation. Nothing on the site sets scroll-behavior, so the browser
jumps; the section carries scroll-margin-top for the fixed nav.

It sits in the hero rather than the nav, in the same fill as Get Beta Access, so
the two read as a pair of equal offers rather than a primary and a fallback.

Note this leaves /try with no inbound link again - see HANDOFF.md.

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
  the movement is opacity, not      a rotating ellipse sweeps a circle, and
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


CYCLE = 2.4  # seconds, one full trip of the shimmer around the ring


def _rays(count=28, cx=130, cy=62, rx=40, ry=18, short=13, long_=20):
    """
    Rays around an ellipse: alternating length, cycling colour, and each one
    lit on a delay taken from its position, so brightness chases around the
    ring rather than every ray breathing in unison.

    The movement is opacity, not geometry. Rotation was tried and removed - a
    turning ellipse sweeps a circle, and this one is wider than it is tall, so
    it climbed into the sub-line above and the logo row below. A shimmer moves
    without the footprint ever changing.
    """
    out = []
    for i in range(count):
        a = (2 * math.pi * i) / count
        ux, uy = math.cos(a), math.sin(a)
        reach = long_ if i % 2 == 0 else short
        delay = -(i / float(count)) * CYCLE
        out.append(
            '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" '
            'style="animation:try-ray %.1fs ease-in-out infinite;'
            'animation-delay:%.2fs"/>' % (
                cx + rx * ux, cy + ry * uy,
                cx + (rx + reach) * ux, cy + (ry + reach) * uy,
                RAY_COLOURS[i % len(RAY_COLOURS)], CYCLE, delay))
    return "".join(out)


# Concatenated, not %-formatted: the style strings are full of literal percent
# signs and every one would need escaping.
GLOW = (
    '<span aria-hidden="true" style="position:absolute;left:50%;top:50%;'
    'width:260px;height:124px;margin-left:-130px;margin-top:-62px;'
    'pointer-events:none">'
    '<svg viewBox="0 0 260 124" focusable="false" '
    'style="width:100%;height:100%;overflow:visible;stroke-width:2.1;'
    'stroke-linecap:round;filter:drop-shadow(0 0 4px rgba(200,130,60,.4));'
    'animation:try-glow 2.6s ease-in-out infinite">' + _rays() + '</svg>'
    '</span>'
)

# The guard string, named once. It is what stops a rebuild adding a second
# button, so it must change in lockstep with the href in TRY_BUTTON below.
TRY_HREF = 'href="/#playground"'

# 26px on top of the row's own 12px gap, on the RIGHT now that Try It comes
# first. The rays reach past the button on every side, and without the extra gap
# they crossed the Get Beta Access button beside it - decoration drawn over a
# different control reads as a rendering fault. The margin has to sit on
# whichever side the neighbour is.
TRY_BUTTON = (
    '<div style="position:relative;display:inline-flex;margin-right:26px">'
    + GLOW +
    '<a href="/#playground" style="position:relative;padding:12px 28px;'
    'border-radius:10px;background:#84512E;color:#F9F9F7;font-size:.9375rem;'
    'font-weight:500;text-decoration:none;white-space:nowrap">Try It</a>'
    '</div>'
)

KEYFRAMES = (
    "\n  /* The hero Try It glow. The group breathes; each ray lights on its own"
    "\n     delay so the brightness travels around the ring. opacity and scale"
    "\n     only - both compositor-only, so 28 animated rays cannot cost layout"
    "\n     on a page already doing scroll-driven work. */"
    "\n  @keyframes try-glow{0%,100%{transform:scale(1)}50%{transform:scale(1.04)}}"
    "\n  @keyframes try-ray{0%,100%{opacity:.2}50%{opacity:1}}\n"
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

        if HERO_CTA in s and TRY_HREF not in s:
            s = s.replace(HERO_CTA, TRY_BUTTON + HERO_CTA, 1)
            added += 1
            if "@keyframes try-glow" not in s:
                s = s.replace("\n</style>", KEYFRAMES + "</style>", 1)

        if s != before:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(s)

    print("  try button: added to %d hero(s), removed from %d nav(s)"
          % (added, removed))
    if added == 0:
        present = any(TRY_HREF in io.open(p, encoding="utf-8", errors="surrogateescape").read()
                      for p in glob.glob(os.path.join(out, "*.html")))
        if not present:
            print("  hero CTA not found - no Try It button - CHECK")
