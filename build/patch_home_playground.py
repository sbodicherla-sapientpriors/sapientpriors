"""
Bring the playground onto the home page, after "What changes".

WHY it moved: it was a separate page reachable only from a nav entry, which put
the one interactive proof on the site behind a click that most readers never
make. The home page argues that memory changes three numbers and then asks the
reader to believe it; the demo is the place they can check. It belongs in the
argument, immediately after the claim.

WHY no data-stage / data-reveal on this section, unlike every other one:

  1. Those attributes are how scroll-motion.js animates a section in, and they
     start it at opacity:0. This section is a jump target — arriving at it by
     hash means arriving without a scroll event, and an entrance that has not
     fired yet leaves the demo invisible on the one page-load that was asking
     for it specifically.
  2. It is also what was asked for: land on the section, do not perform.

WHY the background is #F6F6F4 and not #FFFFFF like the section above it: the
demo's frame carries a legend that sits ON its top border and paints the page
colour over it to break the rule. On a white section that legend would be a
grey chip floating on white instead of a gap in a line.

data-scroll-target names where the Try It anchor should come to rest. The
default in the markup is the heading, because landing on the section's own top
edge put a padding-step of empty background under the nav and pushed the
username card most of the way down the viewport. try-demo.js swaps it to the
demo itself once a username exists, so a returning visitor - who never sees the
gate - is taken straight to the thing they came back for.

The slot is a div inside the <x-dc> template, not appended to the body, because
the runtime replaces the whole subtree on hydration — see the same note in
Playground.dc.html, and the x-dc guard in try-demo.js's mount().
"""
import glob
import io
import os

MONO = ("'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace")

# Kept verbatim from the Playground page it replaces, rather than rewritten:
# the copy was already reviewed and it is the same demo.
SECTION = (
    '\n    <div id="playground" data-home-playground="" data-scroll-target="[data-try-head]" '
    'style="scroll-margin-top:90px;position:relative;border-bottom:1px solid #E4E4E0;'
    'background:#F6F6F4;padding-block:clamp(3.5rem,5vw,5rem) clamp(3rem,5vw,5rem)">\n'
    '      <div style="position:relative;padding-inline:clamp(1.25rem,3.2vw,4.5rem)">\n'
    '        <div data-try-head="" style="max-width:48rem;scroll-margin-top:88px">\n'
    '          <p style="margin:0 0 20px;display:flex;align-items:center;gap:12px;'
    'font-family:' + MONO + ';font-weight:500;font-size:.8125rem;letter-spacing:.14em;'
    'text-transform:uppercase;color:#6B7078">Playground'
    '<span style="height:1px;flex:1;background:#E4E4E0"></span></p>\n'
    '          <h2 style="margin:0;font-family:Newsreader,Georgia,serif;font-weight:400;'
    'font-size:clamp(1.875rem,1rem + 2.7vw,3.5rem);line-height:1.1;letter-spacing:-.018em">'
    'Try it on a document nobody wrote for a demo.</h2>\n'
    '          <p style="margin:20px 0 0;max-width:42rem;'
    'font-size:clamp(1.0625rem,.98rem + .28vw,1.3125rem);line-height:1.6;color:#3A3E45">'
    'A 288-page MG Hector owner’s manual, scanned, sitting on the left. Ask it anything. '
    'The clock reports how long the first word took, and every answer cites the figures it '
    'was read from, so you can check it against the page yourself.</p>\n'
    '        </div>\n'
    '      </div>\n'
    '      <div data-try-mount></div>\n'
    '    </div>\n'
)

ANCHOR = '<div id="how-it-works"'
PAGES = ("index.html", "SapientPriors.dc.html")


def apply(out):
    done = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        if os.path.basename(path) not in PAGES:
            continue
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        # The guard is the section's own marker, so a re-run cannot stack two
        # copies of the demo on one page.
        if 'data-home-playground' in s:
            continue
        i = s.find(ANCHOR)
        if i == -1:
            print("  %s: no how-it-works section - playground NOT placed - CHECK"
                  % os.path.basename(path))
            continue
        s = s[:i] + SECTION + "    " + s[i:]
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        done += 1
    print("  playground section placed on %d pages" % done)
    if done == 0:
        print("  playground placed nowhere - CHECK")
