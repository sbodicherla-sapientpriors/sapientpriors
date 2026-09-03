# -*- coding: utf-8 -*-
"""
Page titles and the tab icon.

Neither existed. Every page shipped with no <title> at all, so browsers fell
back to the bare hostname - a tab read "sapientpriors.com" - and with no icon
declared they drew the generic globe.

The icon is the SP mark, but not the mark as drawn: at 1024px it is a thin
node-and-link monogram sitting in a lot of empty canvas, and rendered straight
into a 16px tab it all but vanished. So it is trimmed to the artwork's own
bounding box rather than its canvas, thickened from stroke-width 12 to 70, and
set light on a dark tile. The tile is the part that matters most - a transparent
icon has to survive both a light and a dark tab strip, and ink-on-nothing loses
one of them.
"""
import glob
import io
import os

# Title per page. The home page is the bare name, everything else is
# "Section - SapientPriors", which is what a tab strip full of them reads best
# as: the distinguishing word first, while the tab is still wide.
TITLES = {
    "index.html": "SapientPriors",
    "SapientPriors.dc.html": "SapientPriors",
    "Careers.dc.html": "Careers — SapientPriors",
    "TryIt.dc.html": "Try it — SapientPriors",
    "Team.dc.html": "Team — SapientPriors",
    "API Docs.dc.html": "Docs — SapientPriors",
    "Research.dc.html": "Research — SapientPriors",
    "Pricing.dc.html": "Pricing — SapientPriors",
    "Company Brain.dc.html": "Company Brain — SapientPriors",
    "Context Management.dc.html": "Context Management — SapientPriors",
    "Continual Learning.dc.html": "Continual Learning — SapientPriors",
}
DEFAULT = "SapientPriors"

# SVG first for anything that takes it, .ico behind it for Safari and older
# clients, which do not.
# The section entrance animations translate horizontally (data-stage-fx="right"
# slides in from the side). Nothing clipped the page, so while one of those is
# mid-flight the document is wider than the viewport and the whole page scrolls
# sideways - measured at 58px on desktop and 16px on a phone.
#
# clip, not hidden: overflow-x:hidden forces the other axis to auto and turns the
# element into a scroll container, which breaks position:sticky. clip does not.
CLIP = "<style>html,body{overflow-x:clip}</style>"

ICONS = (
    '<link rel="icon" href="/favicon.svg" type="image/svg+xml">'
    '<link rel="icon" href="/favicon.ico" sizes="32x32">'
    '<link rel="apple-touch-icon" href="/apple-touch-icon.png">'
)


def apply(out):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        name = os.path.basename(path)
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        if ("<title>" in s and 'rel="icon"' in s
                and "overflow-x:clip" in s):
            continue
        head = s.find("<head>")
        if head == -1:
            print("  %s has no <head> - not titled - CHECK" % name)
            continue
        add = ""
        if "<title>" not in s:
            add += "\n<title>%s</title>" % TITLES.get(name, DEFAULT)
        if 'rel="icon"' not in s:
            add += "\n" + ICONS
        if "overflow-x:clip" not in s:
            add += "\n" + CLIP
        s = s[:head + len("<head>")] + add + s[head + len("<head>"):]
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  titled and iconed %d pages" % n)
    if n == 0:
        print("  no pages took a title - CHECK")
