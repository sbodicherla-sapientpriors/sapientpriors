"""
UI fixes the export reintroduces each time.

1. Hero CTAs are <div onClick> rather than links. "Try it" scrolled to the
   home-page demo instead of opening the Try It page, and "Read the research"
   had no handler at all — a dead button.
2. The nav sits in its own stacking context at z-index 50, while a separate
   fixed hairline sits at z-index 51. The dropdown is z-index 60, but that is
   scoped *inside* the nav's context, so the hairline painted over the open
   menu. Raising the nav above the hairline fixes it; the panel was already
   opaque white, so this was never an opacity problem.
3. Hover opened a menu for every nav group, including Pricing, Research and
   Docs, which have no items — producing an empty white card under them.
4. The cost chart's legend sat below the plot, and no point carried its value.
"""
import os


def apply(out):
    # ---------- nav ----------
    p = os.path.join(out, "SiteNav.dc.html")
    if os.path.exists(p):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        before = s
        s = s.replace(
            '<div style="position:fixed;inset-inline:0;top:0;z-index:50;',
            '<div style="position:fixed;inset-inline:0;top:0;z-index:52;')
        s = s.replace(
            "open: () => this.setState({ menu: g.label }),",
            "open: () => { if (g.items) this.setState({ menu: g.label }); },")
        if s != before:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            print("  SiteNav.dc.html  nav above the hairline, hover only opens real menus")

    _footer(out)
    _nav_groups(out)
    _research_under_construction(out)
    _team_sections(out)
    _pricing_page(out)
    _careers_roles(out)
    _careers_art(out)
    _careers_apply_form(out)
    _api_docs_chrome(out)
    _contact_email(out)

    # ---------- home ----------
    for name in ("SapientPriors.dc.html", "index.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        before = s

        # 0. Curtain: 5.14s down to 4s.
        #
        # Two numbers have to move together or they desynchronise: the CSS lift
        # is 600ms and fires on a delay, and a JS timer unmounts the curtain at
        # CURTAIN_MS. Delay + lift must equal CURTAIN_MS, so 2400 + 600 = 3000.
        #
        # 2400ms is the floor worth going to without recutting the artwork:
        # the sweep rule finishes at 1660ms, so the composed frame still
        # holds for ~0.7s before it lifts. Below about 2.2s the wordmark
        # would start lifting before it had finished arriving.
        #
        # The fallback matters as much as either. The timer does not start
        # until the goldfish video is actually rolling, and if it never plays a
        # 6s fallback kicked in — which would have meant 6s of waiting plus a
        # 4s curtain on exactly the slow connection least able to afford it.
        # 1.5s is long enough for a 428KB local video to start.
        s = s.replace("CURTAIN_MS = 5140", "CURTAIN_MS = 3000")
        s = s.replace("curtain-lift 600ms cubic-bezier(.6,0,.85,.35) 4540ms forwards",
                      "curtain-lift 600ms cubic-bezier(.6,0,.85,.35) 2400ms forwards")
        s = s.replace("this.startCurtain(), 6000)", "this.startCurtain(), 1500)")

        # Curtain: "Forgetting / ends here." over the goldfish film.
        #
        # The accent moves to line one, because the word being negated is the
        # one worth colouring. The italic goes with it: a soft, expressive word
        # followed by an upright verdict reads as a statement, where the
        # reverse reads as a caption.
        L1 = ("font-family:Newsreader,Georgia,serif;font-size:clamp(2.75rem,8.4vw,8.5rem);"
              "line-height:.95;letter-spacing:-.035em;"
              "animation:line-up 860ms cubic-bezier(.16,.84,.24,1) 220ms both")
        L2 = ("font-family:Newsreader,Georgia,serif;font-style:italic;"
              "font-size:clamp(2.75rem,8.4vw,8.5rem);line-height:.95;letter-spacing:-.035em;"
              "color:#84512E;animation:line-up 860ms cubic-bezier(.16,.84,.24,1) 360ms both")
        s = s.replace(L1, L1.replace("font-family:Newsreader,Georgia,serif;",
                                     "font-family:Newsreader,Georgia,serif;font-style:italic;")
                            .replace("letter-spacing:-.035em;",
                                     "letter-spacing:-.035em;color:#84512E;"))
        s = s.replace(L2, L2.replace("font-style:italic;", "").replace("color:#84512E;", ""))
        s = s.replace(">Nothing</div>", ">Forgetting</div>")
        s = s.replace(">forgotten</div>", ">ends here.</div>")

        # One word, with the half that is the name carrying the weight.
        # One word, with the half that is the name carrying the weight.
        #
        # It also needed contrast and air: at #9AA0A8 over the goldfish it was
        # barely visible, and 18px above a 8.5rem headline put it inside the
        # headline's optical space rather than above it.
        # Lift the wordmark out of the centred column and pin it to the top of
        # the curtain. It was sitting on the fish, so the film read through the
        # letterforms and neither was legible - while the top third of the
        # screen was empty. Also drops the mono for the same Newsreader the nav
        # wordmark uses, so the brand looks like itself for the three seconds
        # before the nav appears.
        #
        # Sized to read as the headline's equal rather than to match its
        # font-size. "Forgetting" is ten characters at 8.4vw; SapientPriors
        # is thirteen, so the same font-size would make it a third wider than
        # the line it sits above - bigger, not equal, and past the viewport on
        # a phone. 6.1vw puts the two words at nearly the same measured width,
        # which is what the eye actually compares.
        s = s.replace("margin-bottom:18px;font-family:'JetBrains Mono',monospace;"
                      "font-weight:500;font-size:.75rem;letter-spacing:.3em;"
                      "text-transform:uppercase;color:#9AA0A8;",
                      "position:absolute;top:clamp(2rem,7vh,4.5rem);left:0;right:0;"
                      "text-align:center;font-family:Newsreader,Georgia,serif;"
                      "font-weight:400;font-size:clamp(1.6rem,6.1vw,6.2rem);letter-spacing:-.03em;"
                      "white-space:nowrap;color:#6B7078;")
        s = s.replace(">SapientPriors</div>",
                      ">Sapient<span style=\"font-weight:600;color:#14161A\">Priors</span></div>")

        # Absolute positioning resolves against the nearest positioned
        # ancestor, and the wordmark sat inside the centred column, which is
        # position:relative. So "top: 7vh" measured from the middle of the
        # screen and landed it between the two headline lines. Move the element
        # out to be a direct child of the fixed curtain, which is the box we
        # actually want to measure from.
        import re as _re2
        m = _re2.search(r'<div style="position:absolute;top:clamp\(2rem,7vh,4\.5rem\)[^>]*>'
                       r'Sapient<span[^>]*>Priors</span></div>', s)
        if m:
            mark = m.group(0)
            s = s[:m.start()] + s[m.end():]
            col = s.find('<div style="position:relative;display:flex;flex-direction:column;'
                         'align-items:center;gap:2px">')
            if col != -1:
                s = s[:col] + mark + "\n      " + s[col:]


        # The three buttons under "The lab" are <div>s with cursor:pointer and
        # no href - styled to look clickable, doing nothing. Every one of them
        # has a real page to point at, so this is a dead end at exactly the
        # moment a reader has decided they want to know more.
        for label, href in (("Meet the team", "Team.dc.html"),
                            ("What we're researching", "Research.dc.html"),
                            ("We're hiring", "Careers.dc.html")):
            i = s.find(">%s <span" % label)
            if i == -1:
                print("  lab button %-22s not found - CHECK" % label)
                continue
            j = s.rfind("<div ", 0, i)
            tag = s[j:s.find(">", j) + 1]
            if "cursor:pointer" not in tag:
                continue
            a = (tag.replace("<div ", '<a href="%s" ' % href)
                    .replace("cursor:pointer", "text-decoration:none"))
            end = s.find("</div>", i)
            s = s[:j] + a + s[j + len(tag):end] + "</a>" + s[end + len("</div>"):]

        # The goldfish school: 540 -> 945 (up 75%), and pulled back into frame.
        #
        # This is the only patch that touches the artwork. There were briefly
        # two, both matching the export's own 720px, and the first to run won -
        # so the second was dead code that looked live.
        #
        # It was anchored right:-6%, which hung roughly a tenth of the school
        # past the right edge where the section's overflow:hidden cut it off -
        # so the two fish on the right were sliced in half. Positive inset puts
        # the whole school inside the frame, and at this size it needs to be:
        # a clipped edge reads as a mistake once the artwork is large enough to
        # notice.
        s = s.replace(
            "right:-6%;top:4%;width:min(50vw,720px);aspect-ratio:2/1;"
            "background:url('art/goldfish-school.webp')",
            "right:3%;top:2%;width:min(56vw,945px);aspect-ratio:2/1;"
            "background:url('art/goldfish-school.webp')")

        # "What you can build": six list rows become a 3x2 grid of cards.
        s = _use_cases_as_cards(s)
        if "[data-usecase-card]" not in s:
            s = s.replace("\n</style>", USECASE_CSS + "</style>", 1)

        # The hero headline: "Learns from every conversation. Answers in
        # milliseconds."
        #
        # The old line was a typographic trick - "forgets" struck through,
        # "remembers" fading in after it - which said one thing, that memory is
        # missing. It never mentioned that personalisation normally costs
        # latency, which is the objection a technical buyer actually raises and
        # the one thing worth answering above the fold.
        #
        # The stagger goes with it. The struck word needed 1.1s to draw and the
        # replacement landed at 1.5s, because the joke had to be read in order.
        # A headline promising milliseconds that assembles itself over a second
        # and a half undercuts its own claim, so the line now arrives whole on
        # the h1's own fade-up.
        #
        # The accent stays on the second clause: same colour the replacement
        # word carried, now marking the half of the sentence that is the
        # differentiated claim.
        i = s.find('<h1 class="fade-up"')
        if i == -1:
            print("  hero headline not found - CHECK")
        else:
            open_end = s.find(">", i) + 1
            close = s.find("</h1>", open_end)
            s = (s[:open_end]
                 + "Learns from every conversation. "
                 + '<span style="color:#6C4126">Answers in milliseconds.</span>'
                 + s[close:])

        # The sub-line said "Preferences learned from real conversations", which
        # is now the headline verbatim. Repeating it in the next breath makes
        # the page sound like it only has one idea.
        s = s.replace(
            "We build the memory layer it's missing. Preferences learned from real "
            "conversations, recalled in a single call, and sharper every week.",
            "We build the memory layer it's missing. Preferences recalled in a single "
            "call, and sharper every week.")

        # "stick" was doing the work of "remember" without saying it.
        s = s.replace("Watch it stick.", "Watch it remember.")

        # Remove the fixed section rail on the left ("02 / 08" plus dots).
        # It duplicated the nav for orientation the page does not need, and on
        # narrower viewports it sat over the content it was indexing.
        import re as _re
        m = _re.search(r'<div data-section-rail=""[^>]*>', s)
        if m:
            depth, end = 0, m.start()
            for mm in _re.finditer(r"<div\b[^>]*>|</div>", s[m.start():]):
                end = m.start() + mm.end()
                depth += 1 if mm.group(0).startswith("<div") else -1
                if depth == 0:
                    break
            s = s[:m.start()] + s[end:]

        # The hero kicker repeated the wordmark that is already in the nav
        # directly above it, so the first thing under the logo was the logo.
        s = _re.sub(
            r'<p class="fade-up" style="margin:0 0 24px;font-family:\'JetBrains Mono\'[^"]*">SapientPriors</p>',
            "", s)

        # The hero trust line claimed a LoCoMo score and "REST, no SDK
        # required" one line under the buttons. Removed at your request; the
        # provider marks beside it still carry the compatibility point.
        s = _re.sub(
            r'<p style="[^"]*"><span style="color:#6B7078">91\.6 on LoCoMo</span>'
            r'<span aria-hidden="true">·</span><span>REST, no SDK required</span></p>',
            "", s)

        # The dotted brown 100% rule spanned the plot at the cost axis's own
        # 100x gridline, which is a different quantity from the 100% on the
        # right-hand accuracy axis it appeared to belong to. Two unrelated
        # meanings for one horizontal line at one height; removed.
        s = _re.sub(r'<line x1="0" y1="30\.2"[^>]*></line>', "", s)
        s = _re.sub(r'<line x1="0" y1="30\.2"[^>]*>', "", s)

        # Both series were thin enough to disappear against the grid.
        s = s.replace('stroke="{{ s.colour }}" stroke-width="2.5"',
                      'stroke="{{ s.colour }}" stroke-width="3.5"')
        s = s.replace('stroke="{{ a.colour }}" stroke-width="1.75"',
                      'stroke="{{ a.colour }}" stroke-width="2.75"')

        # (careers art is handled per-page in _careers_art)

        # The two curtain corner labels. They named the product category in
        # the corners of a three-second title card nobody reads the corners of.
        s = _re.sub(r'<div style="[^"]*curtain-label[^"]*">(?:Stateful memory|Continual learning)</div>',
                    "", s)

        # 1. hero CTAs
        s = s.replace('<div onClick="{{ goDemo }}"', '<div onClick="{{ goTryIt }}"')
        s = s.replace('>Read the research</div>', '>Read the research</div>')
        s = s.replace(
            "      goDemo: () => this.scrollTo('demo'),",
            "      goDemo: () => this.scrollTo('demo'),\n"
            "      goTryIt: () => { window.location.href = 'TryIt.dc.html'; },\n"
            "      goResearch: () => { window.location.href = 'Research.dc.html'; },")

        # "Read the research" carried no handler at all.
        i = s.find(">Read the research<")
        if i != -1:
            j = s.rfind("<div ", 0, i)
            if j != -1 and "onClick" not in s[j:i]:
                s = s[:j] + '<div onClick="{{ goResearch }}" ' + s[j + len("<div "):]

        # 4a. legend above the plot
        legend_start = s.find('<span style="', s.find("Cost &middot; solid") if "Cost &middot; solid" in s else s.find("Cost · solid"))
        marker = "Cost · solid"
        li = s.find(marker)
        if li != -1 and "data-chart-legend" not in s:
            # the legend is the div two levels up from the marker span
            span = s.rfind("<span", 0, li)
            col = s.rfind("<div", 0, span)
            row = s.rfind("<div", 0, col)
            end = _match(s, row)
            legend = s[row:end]
            s = s[:row] + s[end:]
            legend = legend.replace("<div", '<div data-chart-legend', 1)
            # re-insert directly above the plot block
            anchor = s.find('<div style="display:flex;gap:12px">')
            if anchor != -1:
                s = s[:anchor] + legend + "\n              " + s[anchor:]

        # 4b. value labels overlaid on the plot
        if "chartLabels" not in s:
            s = s.replace(
                '<div style="flex:1;min-width:0">',
                '<div style="flex:1;min-width:0;position:relative">', 1)
            overlay = (
                '\n                  <div aria-hidden="true" style="position:absolute;inset:0;'
                'pointer-events:none">\n'
                '                    <sc-for list="{{ chartLabels }}" as="l" hint-placeholder-count="10">\n'
                '                      <span style="position:absolute;left:{{ l.left }};top:{{ l.top }};'
                'transform:translate(-50%,-50%);padding:1px 5px;border-radius:4px;'
                'background:rgba(255,255,255,.92);font-family:\'JetBrains Mono\',monospace;'
                'font-size:.625rem;line-height:1.5;font-weight:500;color:{{ l.colour }};'
                'white-space:nowrap">{{ l.text }}</span>\n'
                '                    </sc-for>\n'
                '                  </div>')
            # Anchor to the chart's own svg: find() alone lands on the first
            # </svg> in the document, which is an icon far earlier in the page.
            a = s.find('aria-label="Cost growth')
            k = s.find("</svg>", a) if a != -1 else -1
            if k != -1:
                s = s[:k + len("</svg>")] + overlay + s[k + len("</svg>"):]

            s = s.replace("      cost: COST.map(s => ({", CHART_LABELS_JS + "      cost: COST.map(s => ({")

        if s != before:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            print("  " + name + "  hero links, legend on top, point values")


def _match(s, start):
    """Index just past the </div> closing the <div> that opens at `start`."""
    import re
    depth, i = 0, start
    for m in re.finditer(r"<div\b[^>]*>|</div>", s[start:]):
        i = start + m.end()
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            return i
    return -1


# Placed labels, de-overlapped.
#
# The plot is drawn with preserveAspectRatio="none", so the x axis is stretched
# to the container and any <text> inside the SVG would be squashed with it.
# These are HTML instead, positioned as a percentage across and in pixels down
# — the viewBox is 260 tall and so is the rendered box, so y maps 1:1.
#
# Every series starts at the same point (1x cost, 100% accuracy), so without a
# dedupe six labels stack exactly on top of each other at week one. Endpoints
# are placed first because they carry the argument; anything that cannot be
# placed without colliding is dropped rather than nudged, since a value nudged
# away from its own point is worse than no value at all.
CHART_LABELS_JS = """      chartLabels: (() => {
        const out = [], placed = [];
        const cand = [];
        const push = (series, yOf, fmt, dy) => series.forEach(s => {
          s.values.forEach((v, i) => {
            cand.push({
              x: 10 + (i / (s.values.length - 1)) * 780,
              y: yOf(v) + dy,
              text: fmt(v), colour: s.colour,
              prio: i === s.values.length - 1 ? 0 : (i === 0 ? 2 : 1),
              mag: v
            });
          });
        });
        push(COST, v => 250 - (Math.log(v) / Math.log(300)) * 240, v => v + '\\u00d7', -13);
        push(ACCURACY, v => 16 + ((100 - v) / 75) * 234, v => v + '%', 15);

        cand.sort((a, b) => a.prio - b.prio || b.mag - a.mag);
        cand.forEach(c => {
          const w = (18 + String(c.text).length * 9) / 0.82;
          const hit = placed.some(p =>
            Math.abs(p.x - c.x) < (w + p.w) / 2 + 4 && Math.abs(p.y - c.y) < 19);
          if (hit) return;
          placed.push({ x: c.x, y: c.y, w: w });
          out.push({
            left: (c.x / 800 * 100).toFixed(2) + '%',
            top: c.y.toFixed(1) + 'px',
            text: c.text, colour: c.colour
          });
        });
        return out;
      })(),

"""


def _footer(out):
    """Drop the footer tagline — it restates the hero in weaker words."""
    import os
    p = os.path.join(out, "SiteFooter.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    old = ('<p style="margin:0 0 20px;max-width:20rem;font-size:1rem;line-height:1.6;'
           'color:#6B7078">Memory and continual learning for applications that should '
           'stop forgetting.</p>')
    if old in s:
        s = s.replace(old, "")
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  SiteFooter.dc.html  tagline removed")


def _careers_art(out):
    """
    The school of fish on the careers page sat small in the top-right corner.
    2.5x, as asked: 34vw/460px -> 85vw/1150px. Opacity drops from .45 to .28 at
    the same time — the same ink over three times the area would otherwise go
    from an accent to the loudest thing on the page.
    """
    import os
    p = os.path.join(out, "Careers.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    old = "width:min(34vw,460px);aspect-ratio:2/1"
    if old in s:
        s = s.replace(old, "width:min(85vw,1150px);aspect-ratio:2/1")
        s = s.replace("background:url('art/goldfish-school.webp') center/contain no-repeat;"
                      "filter:brightness(1.12) contrast(1.34) saturate(.9);"
                      "mix-blend-mode:multiply;opacity:.45",
                      "background:url('art/goldfish-school.webp') center/contain no-repeat;"
                      "filter:brightness(1.12) contrast(1.34) saturate(.9);"
                      "mix-blend-mode:multiply;opacity:.28")
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  Careers.dc.html  fish scaled 2.5x, opacity eased")


def _nav_groups(out):
    """
    Fold Research under a Docs dropdown.

    Research and Docs were two separate top-level links pointing at two pages a
    reader would go to for the same reason: to understand how the thing works
    before committing. Product keeps the three products, Company keeps the
    people, Docs now keeps everything you read.
    """
    import os
    p = os.path.join(out, "SiteNav.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if OLD_GROUPS in s:
        s = s.replace(OLD_GROUPS, NEW_GROUPS)
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  SiteNav.dc.html  Research folded into a Docs dropdown")


OLD_GROUPS = """  { label: 'Pricing', href: HOME + '#access' },
  { label: 'Research', href: 'Research.dc.html' },
  { label: 'Docs', href: 'API%20Docs.dc.html' },"""

NEW_GROUPS = """  { label: 'Pricing', href: HOME + '#access' },
  { label: 'Docs', items: [
    { label: 'API docs', href: 'API%20Docs.dc.html', description: 'Endpoints, limits and examples' },
    { label: 'Research', href: 'Research.dc.html', description: 'What we are working on, and what we have not solved' }
  ] },"""


def _research_under_construction(out):
    """
    Rebuild Research as an under-construction page.

    Generated from Company Brain rather than hand-written, so it inherits the
    same layout, the same mascot and any future change to that template. The
    old page described four research threads and promised numbers; keeping it
    while nothing is published was the same overclaim as "we publish what we
    learn".
    """
    import os
    src = os.path.join(out, "Company Brain.dc.html")
    dest = os.path.join(out, "Research.dc.html")
    if not os.path.exists(src):
        return
    s = open(src, encoding="utf-8", errors="surrogateescape").read()

    s = s.replace(">Company Brain<", ">Research<")
    s = s.replace(
        "One shared memory across every tool a company runs, so what one team "
        "learns the next one already knows. We're writing it up properly rather "
        "than shipping a placeholder full of adjectives.",
        "How a system decides what to keep, what to surface and what to let go. "
        "We are writing this up properly rather than shipping a placeholder full "
        "of adjectives — and we would rather publish nothing than publish a "
        "number we cannot stand behind.")
    s = s.replace('<dc-import name="SiteNav" active="Product"',
                  '<dc-import name="SiteNav" active="Docs"')
    open(dest, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  Research.dc.html  rebuilt as under construction, with the mascot")


TEAM_DATA = """const TEAM = [
  { group: 'Founders', name: 'Raveeshu Pahuja', role: 'Founder', prior: 'Microsoft \u00b7 Twitter \u00b7 Dropbox', linkedin: 'https://www.linkedin.com/in/raveeshu-pahuja-82b77924/' },
  { group: 'Founders', name: 'Karankumar Sabhnani', role: 'Founder', prior: '84.51\u00b0 \u00b7 Twitter \u00b7 Univ. of Delaware', linkedin: 'https://www.linkedin.com/in/ksabhnani' },
  { group: 'Research engineering', name: 'Eshwar SR', role: 'Research Engineer', prior: 'Indian Institute of Science \u00b7 KENOME \u00b7 Intuit', linkedin: 'https://www.linkedin.com/in/eshwarsr' },
  { group: 'Research engineering', name: 'Siva Krishna', role: 'Research Engineer', prior: 'Spotmies \u00b7 Aegion Dynamic Solutions', linkedin: 'https://www.linkedin.com/in/siva-krishna-07a91a280/' },
  { group: 'Research engineering', name: 'Srinivas Raghav V C', role: 'Research Engineer', prior: 'TCS Research', linkedin: 'https://www.linkedin.com/in/srinivas-raghav-v-c-5aa655260/' },
  { group: 'Research engineering', name: 'Yashwanth Erukulla', role: 'Research Engineer', prior: 'Samsung Research', linkedin: 'https://www.linkedin.com/in/yashwanth-erukulla/' },
  { group: 'Research engineering', name: 'Neelesh Gupta', role: 'Research Engineer', prior: 'ISRO \u00b7 OpenNLP Labs', linkedin: 'https://www.linkedin.com/in/neelesh-gupta-92b2bb2b5/' },
  { group: 'Founders office', name: 'SriHarsha Bodicherla', role: 'Founders Office', prior: 'ISRO / NRSC', linkedin: 'https://in.linkedin.com/in/sriharsha-bodicherla' }
];"""

GROUP_HEADING = ('<h2 style="margin:0 0 20px;font-family:\'JetBrains Mono\',monospace;'
                 'font-weight:500;font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;'
                 'color:#6B7078">LABEL</h2>')


def _team_sections(out):
    """
    Split the team into Founders, Research engineering and Founders office.

    One flat grid of eight made the founders indistinguishable from everyone
    else, and a reader scanning for "who runs this" had to read every card.
    Three labelled groups answer it at a glance.

    Also drops the headcount from the headline. "Eight people" invites the
    reader to decide whether eight is enough before they have read what the
    eight have built, and it dates the page the moment anyone joins.
    """
    import os
    import re as _re
    p = os.path.join(out, "Team.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if "group: 'Founders'" in s:
        return

    # data
    i = s.find("const TEAM = [")
    if i == -1:
        return
    s = s[:i] + TEAM_DATA + s[s.index("];", i) + 2:]

    # headline
    s = s.replace("Eight people, and a memory problem worth a decade.",
                  "A memory problem worth a decade.")

    # three grids in place of one
    i = s.find('<sc-for list="{{ team }}"')
    start = s.rfind("<div", 0, i)
    depth, end = 0, start
    for m in _re.finditer(r"<div\b[^>]*>|</div>", s[start:]):
        end = start + m.end()
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            break
    grid = s[start:end]

    blocks = []
    for label, binding in (("Founders", "founders"),
                           ("Research engineering", "engineers"),
                           ("Founders office", "office")):
        b = grid.replace('list="{{ team }}"', 'list="{{ %s }}"' % binding)
        pad = "" if not blocks else 'margin-top:56px;'
        blocks.append(GROUP_HEADING.replace("LABEL", label).replace("margin:0 0 20px",
                      "margin:%s0 20px" % pad) + b)
    s = s[:start] + "\n            ".join(blocks) + s[end:]

    # Bindings. The existing binding maps TEAM into the card shape, so the
    # three groups filter and reuse that same mapper rather than duplicating
    # it — one place to change if a card ever gains a field.
    old_map = "      team: TEAM.map(p => ({"
    new_map = ("      founders: card(TEAM.filter(p => p.group === 'Founders')),\n"
               "      engineers: card(TEAM.filter(p => p.group === 'Research engineering')),\n"
               "      office: card(TEAM.filter(p => p.group === 'Founders office')),\n"
               "      team: card(TEAM),\n"
               "      _unused: TEAM.map(p => ({")
    if old_map in s:
        s = s.replace(old_map, new_map)
        s = s.replace("class Component extends DCLogic {",
                      "const card = list => list.map(p => ({\n"
                      "  name: p.name,\n"
                      "  role: p.role,\n"
                      "  hasRole: !!p.role,\n"
                      "  prior: p.prior,\n"
                      "  hasPrior: !!p.prior,\n"
                      "  linkedin: p.linkedin,\n"
                      "  initials: p.name.split(' ').filter(w => w.length > 1)"
                      ".slice(0, 2).map(w => w.charAt(0)).join('')\n"
                      "}));\n\nclass Component extends DCLogic {")

    # The grid drew its dividers by showing a grey container through 1px gaps.
    # That works only when every row is full — and now that the team is split
    # into groups of 2, 5 and 1, the leftover cells rendered as grey blanks.
    # The container goes white and each card carries its own hairline instead,
    # so a short row simply ends.
    s = s.replace("gap:1px;overflow:hidden;border-radius:10px;border:1px solid #E4E4E0;"
                  "background:#E4E4E0",
                  "gap:1px;overflow:hidden;border-radius:10px;border:1px solid #E4E4E0;"
                  "background:#FFFFFF")
    s = s.replace("display:flex;flex-direction:column;gap:16px;background:#FFFFFF;"
                  "padding:clamp(1.5rem,2vw,2rem)",
                  "display:flex;flex-direction:column;gap:16px;background:#FFFFFF;"
                  "outline:1px solid #E4E4E0;padding:clamp(1.5rem,2vw,2rem)")

    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  Team.dc.html  split into Founders / Research engineering / Founders office")


def _pricing_page(out):
    """
    Give Pricing its own under-construction page.

    It pointed at the home page's #access anchor, so clicking "Pricing" landed
    a visitor on a contact form having answered nothing about price. An honest
    "not published yet" is a better answer than a form: it tells them the
    information exists and is coming, rather than implying they must book a
    call to find out what it costs.
    """
    import os
    src = os.path.join(out, "Company Brain.dc.html")
    dest = os.path.join(out, "Pricing.dc.html")
    if not os.path.exists(src):
        return
    s = open(src, encoding="utf-8", errors="surrogateescape").read()
    s = s.replace(">Company Brain<", ">Pricing<")
    s = s.replace(
        "One shared memory across every tool a company runs, so what one team "
        "learns the next one already knows. We're writing it up properly rather "
        "than shipping a placeholder full of adjectives.",
        "We are still working out what is fair to charge for a memory layer that "
        "gets cheaper to run as it learns. Rather than publish a number we would "
        "have to walk back, we would rather talk it through against your actual "
        "volume.")
    s = s.replace('<dc-import name="SiteNav" active="Product"',
                  '<dc-import name="SiteNav" active="Pricing"')
    open(dest, "w", encoding="utf-8", errors="surrogateescape").write(s)

    for f in ("SiteNav.dc.html", "SiteFooter.dc.html"):
        p = os.path.join(out, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8", errors="surrogateescape").read()
        if "label: 'Pricing', href: HOME + '#access' }" in t:
            t = t.replace("label: 'Pricing', href: HOME + '#access' }",
                          "label: 'Pricing', href: 'Pricing.dc.html' }")
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(t)
    print("  Pricing.dc.html  created; nav and footer repointed")


NEW_ROLES = """  {
    id: 'founders-office',
    title: 'Founders Office',
    type: 'Full-time',
    location: 'Bangalore, India',
    description: 'Work directly with the founders across research, go-to-market and everything that does not yet have an owner. The full description is not published yet \\u2014 tell us what you would want to own and we will take it from there.',
    responsibilities: [],
    requirements: [],
    preferred: [],
    benefits: []
  },
  {
    id: 'software-engineer',
    title: 'Software Engineer',
    type: 'Full-time',
    location: 'Bangalore, India',
    description: 'Build the API, the infrastructure and the tooling around the memory layer. The full description is not published yet \\u2014 tell us what you have built and we will take it from there.',
    responsibilities: [],
    requirements: [],
    preferred: [],
    benefits: []
  }
];"""


def _careers_roles(out):
    """
    Rename the intern role in full, and add the two roles without a JD yet.

    A role with no published description still belongs on the page: the point
    of a careers page is to tell someone the seat exists. Empty detail blocks
    would render as four bare headings, so blocks with no items are filtered
    out and the description carries the whole message.
    """
    import os
    p = os.path.join(out, "Careers.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if "founders-office" in s:
        return

    s = s.replace("title: 'ML Engineer Intern',",
                  "title: 'Machine Learning Engineer Intern',")

    # Append the two pending roles. The last existing entry closes with "}"
    # and no trailing comma, so the separator has to be added here — getting
    # this wrong produces "} {" and the whole component fails to parse, which
    # takes the entire careers page down rather than just the new roles.
    i = s.find("const JOBS = [")
    end = s.index("];", i)
    head = s[:end].rstrip()
    body = NEW_ROLES[NEW_ROLES.index("  {"):]
    s = head + ",\n" + body + s[end + 2:]

    # drop empty detail blocks so a pending role shows its description alone
    s = s.replace(
        "        { heading: 'What you get', items: wrap(job.benefits) }\n      ]",
        "        { heading: 'What you get', items: wrap(job.benefits) }\n"
        "      ].filter(b => b.items.length > 0)")

    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  Careers.dc.html  intern renamed; Founders Office and Software Engineer added")


def _careers_apply_form(out):
    """
    Replace the "How to apply" mailto panel with the real application form.

    The panel asked for a CV and a paragraph and gave an email address, which
    means every application arrived as free-form mail that someone had to read,
    retype and file. Nothing reached the CRM, nothing could be filtered, and
    two people applying for different roles were indistinguishable until you
    opened them.

    The form posts to /api/apply, which submits to the "Careers — role
    application" form in HubSpot: its own GUID, its own notification, separate
    from the sales one so applications can be reported on as applications.

    Only the mount point goes in here; apply-form.js builds the form. It is a
    plain module rather than a dc component because the runtime strips
    `required` from inputs, so anything relying on native validation reports an
    empty form as valid - the same bug that made the contact form silently
    discard leads.
    """
    import os
    p = os.path.join(out, "Careers.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if "data-apply-form" in s:
        return

    i = s.find("<p style=\"margin:0 0 10px;font-family:'JetBrains Mono',monospace;"
               "font-weight:500;font-size:.8125rem;letter-spacing:.14em;"
               "text-transform:uppercase;color:#A3A3A0\">How to apply</p>")
    if i == -1:
        print("  Careers.dc.html  'How to apply' panel not found - CHECK")
        return
    # walk out to the dark panel that wraps it, then past its closing tag
    start = s.rfind('<div style="margin-top:36px;border-radius:10px;background:#14161A', 0, i)
    if start == -1:
        print("  Careers.dc.html  apply panel wrapper not found - CHECK")
        return
    depth, k = 0, start
    while k < len(s):
        if s.startswith("<div", k):
            depth += 1
        elif s.startswith("</div>", k):
            depth -= 1
            if depth == 0:
                k += len("</div>")
                break
        k += 1

    mount = ('<div data-apply-form style="margin-top:56px;scroll-margin-top:96px" '
             'id="apply"></div>')
    s = s[:start] + mount + s[k:]

    # the two "Apply by email" buttons in the hero now have somewhere real to go
    s = s.replace('<a href="mailto:contact@sapientpriors.com?subject=Application"',
                  '<a href="#apply"')
    s = s.replace(">Apply by email<", ">Apply now<")

    if "apply-form.js" not in s:
        j = s.rfind("</body>")
        tag = '<script src="apply-form.js" defer></script>\n'
        s = (s[:j] + tag + s[j:]) if j != -1 else (s + tag)

    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  Careers.dc.html  application form replaces the mailto panel")


def _close_div(s, start):
    """Index just past the </div> that closes the <div> opening at `start`."""
    depth, k = 0, start
    while k < len(s):
        if s.startswith("<div", k):
            depth += 1
        elif s.startswith("</div>", k):
            depth -= 1
            if depth == 0:
                return k + len("</div>")
        k += 1
    return -1


def _api_docs_chrome(out):
    """
    Give the API docs page the site's own nav and footer.

    It was exported as a standalone shell: its own fixed header carrying only
    "Product" and "Research" - both pointing at the home page rather than at
    Research.dc.html - and a two-line footer with a copyright and a mailto.
    So it had no Pricing, no Company, no Docs dropdown, no legal links, and two
    nav items that went to the wrong place. Landing on it felt like landing on
    an older version of the site, because structurally it was one.

    Swapping in the shared components fixes it permanently: SiteNav is
    position:fixed at the same 72px height the page already pads for, so this
    is a straight substitution, and every future nav change reaches this page
    without anyone remembering it exists.
    """
    import os
    p = os.path.join(out, "API Docs.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    if "dc-import name=\"SiteNav\"" in s:
        return

    head = ('<div style="position:fixed;inset-inline:0;top:0;z-index:50;'
            'border-bottom:1px solid #E4E4E0;background:rgba(246,246,244,.85);'
            'backdrop-filter:blur(12px)">')
    i = s.find(head)
    if i == -1:
        print("  API Docs.dc.html  inline header not found - CHECK")
    else:
        end = _close_div(s, i)
        s = (s[:i]
             + '<dc-import name="SiteNav" active="Docs" hint-size="100%,72px"></dc-import>'
             + s[end:])

    foot = ('<div style="border-top:1px solid #E4E4E0;'
            'padding-inline:clamp(1.25rem,3.2vw,4.5rem);padding-block:32px;'
            'display:flex;flex-wrap:wrap;align-items:center;'
            'justify-content:space-between;gap:12px">')
    j = s.find(foot)
    if j == -1:
        print("  API Docs.dc.html  inline footer not found - CHECK")
    else:
        end = _close_div(s, j)
        s = (s[:j]
             + '<dc-import name="SiteFooter" hint-size="100%,420px"></dc-import>'
             + s[end:])

    open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
    print("  API Docs.dc.html  now uses the shared nav and footer")


USECASE_CSS = """
  [data-usecase-card]{transition:transform 160ms cubic-bezier(.16,1,.3,1),box-shadow 160ms ease-out,border-color 160ms ease-out}
  [data-usecase-card]:hover{transform:translateY(-4px);box-shadow:0 14px 30px -14px rgba(20,22,26,.22);border-color:#CFCFC9}
  @media (prefers-reduced-motion:reduce){
    [data-usecase-card]{transition:none}
    [data-usecase-card]:hover{transform:none}
  }
  @media (max-width:1180px){
    [data-usecase-grid]{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  }
  @media (max-width:720px){
    [data-usecase-grid]{grid-template-columns:minmax(0,1fr)!important}
  }
"""


def _use_cases_as_cards(s):
    """
    Turn the "What you can build" accordion into a grid of cards.

    A six-row list of one-liners reads as a table of contents: nothing to look
    at, and the eye runs down the left edge rather than across the six things
    we are claiming. Three across and two down makes it a set, which is what it
    actually is.

    The detail each row hid - the scenario, what it learns, the outcome, the API
    flow - is kept and opens inside its own card. Grid rows size to their
    tallest cell, so an opened card grows its row and the others hold position.
    Dropping that content would have been the easy way to make the grid tidy and
    would have cost the section the only concrete thing in it.

    Hover lift lives in a stylesheet rule because inline styles cannot express
    :hover, and it is disabled under prefers-reduced-motion.

    It carries its own breakpoints rather than the page's data-cols-3, which
    drops to two columns at 1440 - that would mean a 1280px laptop, the most
    common screen there is, never sees the three-across this was asked for.
    Three holds to 1180, then two, then one.
    """
    start = s.find('<div style="margin:56px auto 0;max-width:56rem">')
    if start == -1:
        print("  use-case accordion container not found - CHECK")
        return s
    end = _close_div(s, start)
    block = s[start:end]

    a = block.find('<sc-if value="{{ u.open }}"')
    b = block.find("</sc-if>", a)
    if a == -1 or b == -1:
        print("  use-case detail block not found - CHECK")
        return s
    detail = block[a:b + len("</sc-if>")]
    # the detail was indented under a 56px-wide number column; in a card it is
    # full width under a rule
    detail = detail.replace('style="padding:0 16px 24px 56px;',
                            'style="margin-top:4px;padding:16px 0 0;'
                            'border-top:1px solid #EFEFEC;')

    card = (
        '<div data-usecase-card onClick="{{ u.toggle }}" '
        'style="display:flex;flex-direction:column;gap:14px;border:1px solid #E4E4E0;'
        'border-radius:12px;background:#FFFFFF;padding:24px;cursor:pointer">\n'
        '              <div style="display:flex;align-items:flex-start;'
        'justify-content:space-between;gap:12px">\n'
        '                <div style="width:40px;height:40px;border-radius:10px;'
        'background:rgba(132,81,46,.1);display:flex;align-items:center;'
        'justify-content:center;flex-shrink:0;font-family:\'JetBrains Mono\',monospace;'
        'font-size:.8125rem;font-weight:500;color:#84512E">{{ u.num }}</div>\n'
        '                <span style="color:#9AA0A8;flex-shrink:0;font-size:.875rem">'
        '{{ u.chevron }}</span>\n'
        '              </div>\n'
        '              <div>\n'
        '                <h3 style="margin:0;font-size:1.125rem;font-weight:600;'
        'line-height:1.3">{{ u.title }}</h3>\n'
        '                <p style="margin:6px 0 0;font-size:.875rem;line-height:1.55;'
        'color:#6B7078">{{ u.description }}</p>\n'
        '              </div>\n'
        '              ' + detail + '\n'
        '            </div>'
    )

    grid = (
        '<div data-usecase-grid style="margin:56px auto 0;max-width:74rem;'
        'display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;'
        'align-items:start">\n'
        '          <sc-for list="{{ useCases }}" as="u" hint-placeholder-count="6">\n'
        '            ' + card + '\n'
        '          </sc-for>\n'
        '        </div>'
    )
    return s[:start] + grid + s[end:]


def _contact_email(out):
    """
    Swap the public contact address for raveeshu@sapientpriors.io.

    Runs last on purpose. _careers_apply_form still searches for the export's
    own "mailto:contact@sapientpriors.com?subject=Application" to find the
    buttons it replaces, so rewriting the address any earlier would stop that
    match and quietly leave the careers page pointing at an inbox again.

    Note this moves the address to a different top-level domain from everything
    else on the site: the canonical URL, the HubSpot notification recipient and
    the fallback address in the two API routes are all sapientpriors.com. That
    is left alone - only the address asked for is changed.
    """
    import glob
    import os
    old, new = "contact@sapientpriors.com", "raveeshu@sapientpriors.io"
    total, files = 0, 0
    for p in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        n = s.count(old)
        if not n:
            continue
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s.replace(old, new))
        total += n
        files += 1
    print("  contact address -> %s (%d refs across %d files)" % (new, total, files))
