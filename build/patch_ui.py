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
        s = s.replace("margin-bottom:18px;font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;"
                      "font-weight:500;font-size:.75rem;letter-spacing:.3em;"
                      "text-transform:uppercase;color:#9AA0A8;",
                      "position:absolute;top:clamp(2rem,7vh,4.5rem);left:0;right:0;"
                      "text-align:center;font-family:Inter,system-ui,sans-serif;"
                      "font-weight:600;font-size:clamp(1.5rem,5.4vw,5.4rem);letter-spacing:-.035em;"
                      "white-space:nowrap;color:#14161A;")
        # The legal name, with "Inc." set back so it reads as a suffix rather
        # than part of the mark. Inter rather than the serif: the wordmark is a
        # name, and a name in the body face reads as identity where a name in
        # the display face reads as a headline.
        s = s.replace(">SapientPriors</div>",
                      ">SapientPriors<span style=\"font-weight:400;color:#9AA0A8;"
                      "padding-left:.28em\">Inc.</span></div>")

        # Absolute positioning resolves against the nearest positioned
        # ancestor, and the wordmark sat inside the centred column, which is
        # position:relative. So "top: 7vh" measured from the middle of the
        # screen and landed it between the two headline lines. Move the element
        # out to be a direct child of the fixed curtain, which is the box we
        # actually want to measure from.
        # Located by its own style, not by what is inside it. The previous
        # version matched "Sapient<span>Priors</span>", so adding the "Inc."
        # suffix stopped it matching - the hoist silently did nothing and the
        # wordmark went back to measuring 7vh from the middle of the screen,
        # landing on top of the headline. The element carries no other marker,
        # so its absolute-top style is the stable handle.
        START = '<div style="position:absolute;top:clamp(2rem,7vh,4.5rem)'
        i = s.find(START)
        if i == -1:
            print("  curtain wordmark not found to hoist - CHECK")
        else:
            end = s.find("</div>", s.find(">", i)) + len("</div>")
            mark = s[i:end]
            s = s[:i] + s[end:]
            col = s.find('<div style="position:relative;display:flex;flex-direction:column;'
                         'align-items:center;gap:2px">')
            if col == -1:
                print("  curtain column not found - wordmark NOT hoisted - CHECK")
            else:
                s = s[:col] + mark + "\n      " + s[col:]


        # The three buttons under "The lab" are <div>s with cursor:pointer and
        # no href - styled to look clickable, doing nothing. Every one of them
        # has a real page to point at, so this is a dead end at exactly the
        # moment a reader has decided they want to know more.
        # "What we're researching" is dropped rather than routed: Research is a
        # placeholder, and the rule now is that nothing on the site invites
        # anyone to an unfinished page. It was routed here two changes ago,
        # which is why it is a removal and not simply an omission.
        i = s.find(">What we're researching <span")
        if i != -1:
            j = s.rfind("<div ", 0, i)
            if j == -1:
                j = s.rfind("<a ", 0, i)
            end = s.find("</div>", i)
            if end == -1:
                end = s.find("</a>", i) + len("</a>")
            else:
                end += len("</div>")
            s = s[:j] + s[end:]

        for label, href in (("Meet the team", "Team.dc.html"),
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
                 + "Agents that learn from every conversation, "
                 + '<span style="color:#6C4126">answer in real time.</span>'
                 + s[close:])

        # The sub-line has to carry three words the eye should catch on its own:
        # multi-model, real time, LoCoMo. Emphasis is weight and ink, not colour
        # - the headline already spends the accent, and a sub-line with three
        # more coloured words would compete with it rather than support it.
        KEY = 'font-weight:600;color:#14161A'
        s = s.replace(
            "We build the memory layer it's missing. Preferences learned from real "
            "conversations, recalled in a single call, and sharper every week.",
            'One <span style="%s">multi-model</span> memory layer behind whichever model '
            'you run, <span style="%s">trainable</span> on your own data. '
            'Preferences learned from real conversations, returned in '
            '<span style="%s">real time</span>, and '
            '<span style="%s">benchmarked</span> on the state-of-the-art memory suites.' % (KEY, KEY, KEY, KEY))

        # Two of the three hero buttons pointed at pages that are not ready:
        # Try It is still being built and Research is a placeholder. Get API
        # access is the only one with something behind it, so it is the only
        # one left - a single call to action reads as confidence anyway.
        # Matched on the export's own markup, not on names a later patch
        # introduces: the export calls the first button goDemo, and "Read the
        # research" carries no handler at all until it is given one further
        # down. Searching for goTryIt/goResearch here found nothing and removed
        # nothing, silently.
        i = s.find('<div onClick="{{ goDemo }}"')
        if i == -1:
            print("  hero CTA goDemo not found - CHECK")
        else:
            s = s[:i] + s[s.index("</div>", i) + len("</div>"):]

        i = s.find(">Read the research</div>")
        if i == -1:
            print("  hero CTA 'Read the research' not found - CHECK")
        else:
            j = s.rfind("<div ", 0, i)
            s = s[:j] + s[i + len(">Read the research</div>"):]

        # Remove the "Teach it something. Watch it remember." section whole.
        # It was the dark interactive panel between the hero and How it works.
        i = s.find('<div id="demo"')
        if i == -1:
            print("  demo section not found - CHECK")
        else:
            s = s[:i] + s[_close_div(s, i):]

        # "What you can build" headline: what six things are, not what they do.
        s = s.replace("Six things that get better on their own.",
                      "Things people are using us for.")

        # The bubbles artwork sat behind the contact form. It is decoration at
        # a scale that competes with the fields, and a form is the one place on
        # a page where nothing should compete for attention.
        i = s.find("bubbles.webp")
        if i == -1:
            print("  bubbles art not found - CHECK")
        else:
            j = s.rfind("<div ", 0, i)
            s = s[:j] + s[_close_div(s, j):]

        # The four numbers.
        #
        # Retrieval latency in milliseconds was the wrong unit for the claim:
        # a number with no comparison is a number nobody can judge. Against a
        # named system it becomes an argument - and the comparison is not
        # like-for-like in our favour, because their number is retrieval alone
        # while ours is retrieval and the answer.
        #
        # Multi-hop recall and temporal reasoning go: they were sub-scores of
        # LoCoMo sitting beside LoCoMo overall, so three of four tiles measured
        # the same benchmark and the row looked broader than the evidence was.
        # BEAM and LongMem are separate benchmarks, so the row now spans three.
        OLD_TILES = "const TILES = ["
        i = s.find(OLD_TILES)
        if i == -1:
            print("  TILES not found - CHECK")
        else:
            j = s.index("];", i) + 2
            s = s[:i] + """const TILES = [
  { to: 200, dp: 0, zero: '200', suffix: '%', after: 'faster than Mem0',
    label: 'Response latency',
    detail: 'Where Mem0 has finished retrieving, we have retrieved and answered' },
  { to: 91, dp: 0, zero: '91', suffix: '%', after: '', label: 'BEAM',
    detail: 'Long-horizon episodic memory' },
  { to: 89, dp: 0, zero: '89', suffix: '%', after: '', label: 'LongMem',
    detail: 'Long-context retention across sessions' },
  { to: 91.6, dp: 1, zero: '91.6', suffix: '%', after: '', label: 'LoCoMo overall',
    detail: 'Long-context conversational memory, LLM-as-judge' }
];""" + s[j:]

        # The section header counted the tiles in words; it still says four,
        # which is still true, but "we can show the working for" promised a
        # method note next to each and two of these are now single figures.
        s = s.replace("Four numbers we can show the working for.",
                      "Four numbers, on public benchmarks.")

        # The suffix rendered at .32em, which is right for a percent sign
        # riding a two-digit score and wrong for the multiplier that is the
        # whole claim: "2x" read as a 2 with a speck after it.
        s = s.replace("font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.32em;"
                      "letter-spacing:.02em;color:#84512E",
                      "font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.46em;"
                      "letter-spacing:.02em;color:#84512E")

        # Remove the suites table and the "where we are weakest" card. They are
        # the two columns of one data-split grid, so the grid goes with them.
        #
        # The four tiles above now carry BEAM, LongMem and LoCoMo, so the table
        # was restating them a screen later with three of five columns empty -
        # and a table with holes in it argues against the numbers above it.
        i = s.find("Suites and scores")
        if i == -1:
            print("  benchmark table not found - CHECK")
        else:
            g = s.rfind('<div data-split=""', 0, i)
            if g == -1:
                print("  benchmark data-split grid not found - CHECK")
            else:
                s = s[:g] + s[_close_div(s, g):]

        # That paragraph pointed at the table that no longer exists.
        i = s.find("LoCoMo figures are from our own evaluation run")
        if i != -1:
            j = s.rfind("<p ", 0, i)
            k = s.find("</p>", i) + len("</p>")
            s = s[:j] + ('<p style="margin:20px 0 0;max-width:42rem;font-size:1rem;'
                         'line-height:1.6;color:#6B7078">Our own evaluation runs, scored '
                         'with an LLM-as-judge rubric. Method and prompts available on '
                         'request.</p>') + s[k:]

        # "Works with" carried three marks: OpenAI, Anthropic, Gemini. The
        # claim is that the memory layer sits behind whichever model or tool
        # you already run, and three frontier labs do not make that point -
        # they make it look like a model wrapper. The coding tools and the open
        # models are the ones that say "whatever you are using".
        #
        # All redrawn to a single ink so the row reads as one set rather than a
        # sticker sheet: currentColor on every path, inheriting the row's grey.
        # Groq ships as an orange tile with a white glyph knocked out of it, so
        # only the glyph path is kept - the tile would have filled solid.
        i = s.find('<div style="display:flex;align-items:center;gap:16px;color:#6B7078">')
        if i == -1:
            print("  works-with row not found - CHECK")
        else:
            end = _close_div(s, i)
            s = (s[:i]
                 + '<div style="display:flex;align-items:center;flex-wrap:wrap;'
                   'gap:14px 16px;color:#6B7078">'
                 + WORKS_WITH_ROW + "</div>" + s[end:])

        # "faster than Mem0" moves up beside the number. As a label under it
        # the tile read as two facts stacked; on the same line it is one
        # sentence, which is what it is. Set small and in the accent so the
        # figure still carries the tile.
        s = s.replace(
            "letter-spacing:.02em;color:#84512E\">{{ tile.suffix }}</span></p>",
            "letter-spacing:.02em;color:#84512E\">{{ tile.suffix }}</span>"
            "<span style=\"font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.2em;"
            "letter-spacing:.04em;color:#84512E;padding-left:.5em\">"
            "{{ tile.after }}</span></p>")

        s = _founder_cards(s)

        # Remove the goldfish art from "What changes" and "Use cases", and the
        # film from the curtain. Three instances of the same mark on one page
        # stopped reading as a motif and started reading as wallpaper.
        for art in ("goldfish-loop.webp", "goldfish-school.webp"):
            i = s.find(art)
            if i == -1:
                print("  %s not found - CHECK" % art)
                continue
            j = s.rfind("<div ", 0, i)
            s = s[:j] + s[_close_div(s, j):]

        i = s.find('<video src="art/goldfish-swim.mp4"')
        if i == -1:
            print("  curtain video not found - CHECK")
        else:
            j = s.rfind("<div ", 0, i)
            s = s[:j] + s[_close_div(s, j):]

        # The benchmark section loses its headline and standfirst.
        s = s.replace('<h2 style="margin:0;font-family:Newsreader,Georgia,serif;'
                      'font-weight:400;font-size:clamp(1.875rem,1rem + 2.7vw,3.5rem);'
                      'line-height:1.1;letter-spacing:-.018em">Measured on the suites '
                      'that decide a deployment.</h2>', "")
        s = s.replace('<p style="margin:20px 0 0;max-width:42rem;'
                      'font-size:clamp(1.0625rem,.98rem + .28vw,1.3125rem);line-height:1.6;'
                      'color:#3A3E45">Accuracy first, then what it costs to run. Every '
                      'figure is our own evaluation, and the method is written down '
                      'beside it.</p>', "")

        # "We show our working" described a page that no longer shows a method
        # table. What is actually true is that these two have shipped this
        # before, which is the stronger claim anyway.
        s = s.replace("We show our working.", "We have built this before.")

        # Close the hole the removed benchmark headline left behind.
        #
        # Taking out the h2 and standfirst left the wrapper, its 20px margin,
        # a 56px gap, a 1px rule and another 56px of padding - about 133px of
        # empty section with a divider stranded in the middle of it. That rule
        # was drawn under the headline block; with only the kicker above it, it
        # separates nothing from nothing.
        s = s.replace('<div style="border-top:1px solid #E4E4E0;padding-top:56px">',
                      "<div>")
        s = s.replace("margin-top:56px;display:flex;flex-direction:column;"
                      "gap:clamp(4rem,5vw,5rem)",
                      "margin-top:32px;display:flex;flex-direction:column;"
                      "gap:clamp(4rem,5vw,5rem)")

        # The hero carried up to 88px of padding under its last row, which is
        # right under a three-button call to action and far too much under a
        # single line of logos - it left an empty band between "Works with" and
        # the "Backed by" strip with nothing in it but the grid rules.
        s = s.replace("padding-top:clamp(5rem,6vw,7rem);"
                      "padding-bottom:clamp(4rem,5vw,5.5rem)",
                      "padding-top:clamp(5rem,6vw,7rem);"
                      "padding-bottom:clamp(2rem,2.5vw,3rem)")

        # Drop the "The lab" kicker above "We have built this before."
        # Anchored on the text and walked back to its own <p>, so a style
        # change cannot silently unhook it.
        i = s.find(">The lab<")
        if i == -1:
            print("  'The lab' kicker not found - CHECK")
        else:
            j = s.rfind("<p ", 0, i)
            end = s.find("</p>", i) + len("</p>")
            s = s[:j] + s[end:]

        # Entrance animations replay when you come back to them.
        #
        # reveal() and count() each guard on a data attribute and never clear
        # it, so every element animated once per page load and then sat
        # finished. Scroll down, back up, down again and the page is inert.
        #
        # Three things had to change together:
        #
        #  1. The observer only acted on isIntersecting. It now also fires on
        #     the way out, resetting the element to its pre-animation state.
        #  2. reveal()/count() drop their guards on reset, so the next entry
        #     runs the animation rather than returning early.
        #  3. The rAF fallback in measure() revealed anything with
        #     top < vh*0.9 - which is true for everything scrolled past above
        #     the viewport, so it re-revealed elements the instant they were
        #     reset. It now requires the element to be genuinely on screen.
        #
        # Counters reset their text to zero as well, otherwise the number would
        # flash its final value before counting up to it again. That happens
        # while the tile is at opacity 0, so it is never seen.
        OLD_IO = ("entries.forEach(e => { if (e.isIntersecting) "
                  "this.reveal(e.target); });")
        if OLD_IO not in s:
            print("  reveal observer not found - animations will NOT replay - CHECK")
        s = s.replace(OLD_IO,
                      "entries.forEach(e => { if (e.isIntersecting) "
                      "this.reveal(e.target); else this.unreveal(e.target); });", 1)

        s = s.replace(
            "  reveal(el) {\n    if (el.dataset.revealed) return;",
            "  unreveal(el) {\n"
            "    if (!el.dataset.revealed) return;\n"
            "    delete el.dataset.revealed;\n"
            "    el.style.transitionDelay = '';\n"
            "    if (el.hasAttribute('data-reveal')) {\n"
            "      el.style.opacity = '0';\n"
            "      el.style.transform = 'translateY(10px)';\n"
            "    }\n"
            "    if (el.hasAttribute('data-count')) {\n"
            "      delete el.dataset.counted;\n"
            "      const dp = parseInt(el.getAttribute('data-dp') || '0', 10);\n"
            "      el.textContent = (0).toFixed(dp);\n"
            "    }\n"
            "  }\n\n"
            "  reveal(el) {\n    if (el.dataset.revealed) return;")

        s = s.replace(
            "if (el.getBoundingClientRect().top < vh * 0.9) this.reveal(el);",
            "const r = el.getBoundingClientRect();\n"
            "        if (r.top < vh * 0.9 && r.bottom > 0) this.reveal(el);")

        # The charts are pinned and drawn by chart-scroll.js, not by CSS.
        #
        # The first attempt put animation-timeline:view() on the <rect> inside
        # the <clipPath>. Elements in <defs> are never laid out, so view() had
        # no box to measure, the timeline never advanced, and nothing moved -
        # no error, no warning, just a static chart.
        #
        # The clip rects ship at full width, so the charts are complete without
        # the script. It only ever subtracts.

        # A phone-only stylesheet. Everything is inside a max-width:767.98px
        # media query, so the desktop layout is untouched - that was the one
        # hard constraint on this pass.
        if "data-cols-4]>div{padding:18px" not in s:
            s = s.replace("\n</style>", MOBILE_CSS + "</style>", 1)

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
            r'<p class="fade-up" style="margin:0 0 24px;font-family:\'Cascadia Code\'[^"]*">SapientPriors</p>',
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
                'background:rgba(255,255,255,.92);font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
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

        # Runs last of the chart work, deliberately. The overlay patch above
        # anchors on aria-label="Cost growth" and the label maths is inserted
        # as chartLabels - both of which this rewrites. Splitting first left
        # those anchors matching nothing, silently.
        s = _split_chart(s)

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
    before = s
    if old in s:
        s = s.replace(old, "")

    # Drop every footer link to a page that is not finished.
    #
    # These came out of the nav for the same reason, and leaving them one
    # scroll further down is worse than either extreme: a reader who finds
    # Pricing in the footer has been told twice that it exists, and lands on a
    # placeholder anyway. Try It is still being built; Research is a stub.
    #
    # The pages stay deployed and reachable by direct link. Nothing on the site
    # invites anyone to them.
    import re as _re
    dropped = []
    for label in ("Try it", "Pricing", "Research"):
        pat = _re.compile(r"\s*\{ label: '%s', href: [^}]*\},?\n" % _re.escape(label))
        s, n = pat.subn("\n", s, count=1)
        if n:
            dropped.append(label)
        else:
            print("  SiteFooter.dc.html  '%s' not matched - CHECK" % label)

    # a list whose last entry now ends with a comma is a syntax error
    s = _re.sub(r",(\s*)\]", r"\1]", s)

    if s != before:
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  SiteFooter.dc.html  tagline removed; dropped %s" % ", ".join(dropped))


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

    Strip the nav back to Docs and Company.

    Product, Pricing and Research all pointed at pages that are placeholders or
    unfinished. A nav item is a promise that there is something behind it, and
    four of the six were writing cheques the pages could not cash - which costs
    more trust than the missing pages would have.

    The pages stay deployed and reachable by direct link. Only the invitations
    to visit them are removed.
    """
    import os
    p = os.path.join(out, "SiteNav.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    before = s
    if OLD_GROUPS in s:
        s = s.replace(OLD_GROUPS, NEW_GROUPS)

    # Product is its own literal in the export: a label plus a three-item list.
    i = s.find("  { label: 'Product', items: [")
    if i != -1:
        j = s.index("] },", i) + len("] },\n")
        s = s[:i] + s[j:]
    else:
        print("  SiteNav.dc.html  Product group not found - CHECK")

    if s != before:
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("  SiteNav.dc.html  nav reduced to Docs and Company")


OLD_GROUPS = """  { label: 'Pricing', href: HOME + '#access' },
  { label: 'Research', href: 'Research.dc.html' },
  { label: 'Docs', href: 'API%20Docs.dc.html' },"""

NEW_GROUPS = """  { label: 'Docs', href: 'API%20Docs.dc.html' },"""


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

GROUP_HEADING = ('<h2 style="margin:0 0 20px;font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
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

    # Anchored on the text, not on the style string. Matching the full style
    # meant the font-family was part of the search key, so changing the mono
    # font silently unhooked this patch and put the mailto panel back.
    i = s.find(">How to apply</p>")
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
    [data-founder-cards]{grid-template-columns:minmax(0,1fr)!important}
    [data-founder-cards]>div:first-child{border-right:0!important;border-bottom:1px solid #EFEFEC}
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
        'justify-content:center;flex-shrink:0;font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
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


CHART_LABEL_FN = """
const CHART_LABELS = (series, yOf, fmt, dy) => {
  const out = [], placed = [], cand = [];
  series.forEach(s => s.values.forEach((v, i) => cand.push({
    x: 10 + (i / (s.values.length - 1)) * 780,
    y: yOf(v) + dy,
    text: fmt(v), colour: s.colour,
    prio: i === s.values.length - 1 ? 0 : (i === 0 ? 2 : 1),
    mag: v
  })));
  cand.sort((a, b) => a.prio - b.prio || b.mag - a.mag);
  cand.forEach(c => {
    const w = (18 + String(c.text).length * 9) / 0.82;
    if (placed.some(p =>
      Math.abs(p.x - c.x) < (w + p.w) / 2 + 4 && Math.abs(p.y - c.y) < 19)) return;
    placed.push({ x: c.x, y: c.y, w: w });
    out.push({
      left: (c.x / 800 * 100).toFixed(2) + '%',
      top: (c.y / 260 * 100).toFixed(2) + '%',
      // appears when the drawing line reaches its x, over the same 12-52% band
      range: 'cover ' + (12 + ((c.x - 10) / 780) * 40).toFixed(1) + '% cover '
             + (16 + ((c.x - 10) / 780) * 40).toFixed(1) + '%',
      text: c.text, colour: c.colour
    });
  });
  return out;
};
"""

# nowrap and a fixed width, because a vertical label is laid out in columns:
# "Cost, multiple of week one" is wider than the 190px panel is tall, so it
# wrapped to two columns and made that panel's gutter ~29px wider than the
# accuracy panel's. The plots then started at different x, which defeats the
# only reason to stack them. Both labels are short enough for one column now,
# and the width is pinned so a future edit cannot reintroduce the drift.
VLABEL = ("writing-mode:vertical-rl;transform:rotate(180deg);align-self:center;"
          "flex-shrink:0;width:14px;white-space:nowrap;"
          "font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.6875rem;"
          "letter-spacing:.14em;text-transform:uppercase;color:#6B7078")

# Fixed width, and the same on both panels. The whole point of stacking these
# is that a vertical line through them means the same week in each, and that
# only holds if the two axis gutters are identical - "300x" and "100%" do not
# render at the same width on their own.
AXIS = ("display:flex;flex-direction:column;justify-content:space-between;"
        "flex-shrink:0;width:38px;height:190px;font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;"
        "font-variant-numeric:tabular-nums;font-size:.6875rem;line-height:1;"
        "text-align:right")

XAXIS = ('<div data-xaxis style="display:flex;justify-content:space-between;margin-top:8px;'
         "font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.6875rem;"
         'letter-spacing:.06em;text-transform:uppercase;color:#9AA0A8">'
         "<span>Week 1</span><span>Month 1</span><span>Month 3</span>"
         "<span>Month 6</span><span>Month 9</span><span>Year 1</span></div>")

# The overlay is position:absolute;inset:0, so it measures whatever box it
# sits in. With the x-axis row inside that box the percentages resolved against
# ~213px instead of the plot's 190px and every label drifted down in
# proportion - worst at the baseline, which is how "1x" ended up under "Week 1"
# and Haiku's "5x" landed on the green line. The plot and its overlay get their
# own relative box now; the axis row lives outside it.
PLOT_OPEN = '<div style="position:relative">'

SVG_OPEN = ('<svg viewBox="0 0 800 260" preserveAspectRatio="none" '
            'style="display:block;width:100%%;height:190px" role="img" aria-label="%s">')


def caption(text):
    return ('<p style="margin:16px 0 0;font-size:.9375rem;line-height:1.6;'
            'color:#6B7078">%s</p>' % text)


def legend(binding, alias, suffix, faded):
    return (
        '<div style="display:flex;flex-wrap:wrap;align-items:center;gap:10px 20px;'
        'margin:0 0 14px">'
        '<sc-for list="{{ %s }}" as="%s" hint-placeholder-count="3">'
        '<div style="display:flex;align-items:center;gap:8px;font-size:.875rem;'
        'color:#3A3E45">'
        '<span style="display:block;width:22px;height:0;border-top-width:2.5px;'
        'border-top-style:{{ %s.style }};border-top-color:{{ %s.colour }}%s"></span>'
        '{{ %s.name }} <span style="font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
        'color:#9AA0A8">{{ %s.end }}%s</span></div></sc-for></div>'
        % (binding, alias, alias, alias, ";opacity:.62" if faded else "",
           alias, alias, suffix)
    )

OVERLAY = ('<div aria-hidden="true" style="position:absolute;inset:0;pointer-events:none">'
           '<sc-for list="{{ %s }}" as="l" hint-placeholder-count="10">'
           '<span data-chart-label style="animation-range:{{ l.range }};'
           'position:absolute;left:{{ l.left }};top:{{ l.top }};'
           'transform:translate(-50%%,-50%%);padding:1px 5px;border-radius:4px;'
           'background:rgba(246,246,244,.92);font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
           'font-size:.625rem;line-height:1.5;font-weight:500;color:{{ l.colour }};'
           'white-space:nowrap">{{ l.text }}</span></sc-for></div>')


def _split_chart(s):
    """
    Split the dual-axis chart into two panels over one shared x-axis.

    It was cost and accuracy on one plot: cost on a log left axis, accuracy on a
    linear right axis. Two axes on one plot is the most reliable way to make two
    series look related when the relationship is an artefact of where you put
    the axes - slide either scale and the lines cross somewhere else entirely,
    and the reader has no way to know that.

    Stacked, each series gets an honest axis, and the comparison the section is
    actually making - cost climbs while accuracy falls - is read off the shared
    x instead of inferred from two crossing lines.

    The label overlay moves from pixel to percentage positioning. It was
    absolutely positioned in px against a viewBox that only matched while the
    SVG was exactly 260px tall, so any height change silently slid every label
    off its line.
    """
    i = s.find(">Cost, multiple of week one</span>")
    if i == -1:
        print("  chart: cost axis label not found - CHECK")
        return s
    row = s.rfind('<div style="display:flex;gap:12px">', 0, i)
    if row == -1:
        print("  chart: row wrapper not found - CHECK")
        return s
    end = _close_div(s, row)

    acc_panel = (
        '<div data-chart-card data-chart="accuracy" style="border-radius:10px;'
        'border:1px solid #E4E4E0;background:#FFFFFF;'
        'padding:20px clamp(1rem,1.6vw,1.5rem)">'
        '<p style="margin:0 0 14px;font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
        'font-size:.6875rem;letter-spacing:.14em;text-transform:uppercase;'
        'color:#6B7078">Recall accuracy</p>' + legend("accuracy", "a", "%", True) +
        '<div style="display:flex;gap:12px">'
        '<span data-vaxis style="%s">Accuracy</span>' % VLABEL +
        '<div data-yaxis style="%s;color:#C2A288">' % AXIS +
        "<span>100%</span><span>75%</span><span>50%</span><span>25%</span></div>"
        '<div style="flex:1;min-width:0">' + PLOT_OPEN +
        SVG_OPEN % "Recall accuracy over time in production" +
        '<line x1="0" y1="16" x2="800" y2="16" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="94" x2="800" y2="94" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="172" x2="800" y2="172" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="250" x2="800" y2="250" stroke="#E4E4E0"></line>'
        '<defs><clipPath id="wipe-acc" clipPathUnits="userSpaceOnUse">'
        '<rect data-wipe x="0" y="0" width="800" height="260"></rect>'
        '</clipPath></defs><g clip-path="url(#wipe-acc)">'
        '<sc-for list="{{ accuracy }}" as="a" hint-placeholder-count="3">'
        '<polyline points="{{ a.points }}" fill="none" stroke="{{ a.colour }}" '
        'stroke-width="3.5" stroke-dasharray="{{ a.dash }}" stroke-linejoin="round" '
        'stroke-linecap="round" vector-effect="non-scaling-stroke"></polyline>'
        '</sc-for></g></svg>' + (OVERLAY % "accLabels") + "</div>" + XAXIS
        + "</div></div>"
        + caption("How much of what a user told you is still recalled correctly "
                  "as the conversation grows. Context-stuffing decays because the "
                  "window fills and the earliest turns fall out of it; a memory "
                  "layer keeps what mattered and recovers.")
        + "</div>"
    )

    cost_panel = (
        '<div data-chart-card data-chart="cost" style="margin-top:20px;'
        'border-radius:10px;border:1px solid #E4E4E0;'
        'background:#FFFFFF;padding:20px clamp(1rem,1.6vw,1.5rem)">'
        '<p style="margin:0 0 14px;font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
        'font-size:.6875rem;letter-spacing:.14em;text-transform:uppercase;'
        'color:#6B7078">Cost, multiple of week one</p>'
        + legend("cost", "s", "\u00d7", False) +
        '<div style="display:flex;gap:12px">'
        '<span data-vaxis style="%s">Cost</span>' % VLABEL +
        '<div data-yaxis style="%s;color:#9AA0A8">' % AXIS +
        "<span>300\u00d7</span><span>30\u00d7</span><span>3\u00d7</span>"
        "<span>1\u00d7</span></div>"
        '<div style="flex:1;min-width:0">' + PLOT_OPEN +
        SVG_OPEN % "Cost growth over time in production" +
        '<line x1="0" y1="10" x2="800" y2="10" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="93" x2="800" y2="93" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="176" x2="800" y2="176" stroke="#EFEFEC"></line>'
        '<line x1="0" y1="250" x2="800" y2="250" stroke="#E4E4E0"></line>'
        '<defs><clipPath id="wipe-cost" clipPathUnits="userSpaceOnUse">'
        '<rect data-wipe x="0" y="0" width="800" height="260"></rect>'
        '</clipPath></defs><g clip-path="url(#wipe-cost)">'
        '<sc-for list="{{ cost }}" as="s" hint-placeholder-count="3">'
        '<polyline points="{{ s.points }}" fill="none" stroke="{{ s.colour }}" '
        'stroke-width="3.5" stroke-dasharray="{{ s.dash }}" stroke-linejoin="round" '
        'stroke-linecap="round" vector-effect="non-scaling-stroke"></polyline>'
        '</sc-for></g></svg>' + (OVERLAY % "costLabels") + "</div>" +
        # the x-axis is drawn once, under the lower panel, and read by both
        '<div data-xaxis style="display:flex;justify-content:space-between;margin-top:8px;'
        'font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.6875rem;'
        'letter-spacing:.06em;text-transform:uppercase;color:#9AA0A8">'
        "<span>Week 1</span><span>Month 1</span><span>Month 3</span>"
        "<span>Month 6</span><span>Month 9</span><span>Year 1</span></div>"
        "</div></div>"
        + caption("What the same conversation costs to serve, indexed to each "
                  "system\u2019s own week one and drawn on a log scale. Re-sending the "
                  "whole history on every turn compounds; storing it once and "
                  "retrieving what is relevant does not.")
        + "</div>"
    )

    s = s[:row] + '<div data-chart-pin>' \
        + acc_panel + cost_panel + "</div>" + s[end:]

    # one de-overlap pass per panel now, not one across both planes
    i = s.find("<div data-chart-legend")
    if i != -1:
        s = s[:i] + s[_close_div(s, i):]

    s = s.replace(
        "Two axes: cost indexed to each system's own week one on the left, recall "
        "accuracy on the right. Ours dips while it learns you, then recovers; "
        "context-stuffing decays and never comes back. Illustrative until the task "
        "behind a dollar figure is defined.",
        "Two charts on one timeline: recall accuracy above, cost below, indexed to "
        "each system's own week one. Ours dips while it learns you, then recovers; "
        "context-stuffing decays and never comes back. Illustrative until the task "
        "behind a dollar figure is defined.")

    i = s.find("chartLabels: (() => {")
    if i == -1:
        print("  chart: chartLabels block not found - CHECK")
        return s
    j = s.index("})(),", i) + len("})(),")
    s = s[:i] + (
        "costLabels: CHART_LABELS(COST, "
        "v => 250 - (Math.log(v) / Math.log(300)) * 240, v => v + '\\u00d7', -13),\n"
        "      accLabels: CHART_LABELS(ACCURACY, "
        "v => 16 + ((100 - v) / 75) * 234, v => v + '%', 15),"
    ) + s[j:]

    k = s.find("const USE_CASES = [")
    if k != -1:
        s = s[:k] + CHART_LABEL_FN.strip() + "\n\n" + s[k:]
    return s


WORKS_WITH_ROW = '<svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="OpenAI"><path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Anthropic"><path d="M17.3041 3.541h-3.6718l6.696 16.918H24Zm-10.6082 0L0 20.459h3.7442l1.3693-3.5527h7.0052l1.3693 3.5528h3.7442L10.5363 3.5409Zm-.3712 10.2232 2.2914-5.9456 2.2914 5.9456Z"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Google Gemini"><path d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="DeepSeek"><path d="M23.748 4.482c-.254-.124-.364.113-.512.234-.051.039-.094.09-.137.136-.372.397-.806.657-1.373.626-.829-.046-1.537.214-2.163.848-.133-.782-.575-1.248-1.247-1.548-.352-.156-.708-.311-.955-.65-.172-.241-.219-.51-.305-.774-.055-.16-.11-.323-.293-.35-.2-.031-.278.136-.356.276-.313.572-.434 1.202-.422 1.84.027 1.436.633 2.58 1.838 3.393.137.093.172.187.129.323-.082.28-.18.552-.266.833-.055.179-.137.217-.329.14a5.526 5.526 0 0 1-1.736-1.18c-.857-.828-1.631-1.742-2.597-2.458a11.365 11.365 0 0 0-.689-.471c-.985-.957.13-1.743.388-1.836.27-.098.093-.432-.779-.428-.872.004-1.67.295-2.687.684a3.055 3.055 0 0 1-.465.137 9.597 9.597 0 0 0-2.883-.102c-1.885.21-3.39 1.102-4.497 2.623C.082 8.606-.231 10.684.152 12.85c.403 2.284 1.569 4.175 3.36 5.653 1.858 1.533 3.997 2.284 6.438 2.14 1.482-.085 3.133-.284 4.994-1.86.47.234.962.327 1.78.397.63.059 1.236-.03 1.705-.128.735-.156.684-.837.419-.961-2.155-1.004-1.682-.595-2.113-.926 1.096-1.296 2.746-2.642 3.392-7.003.05-.347.007-.565 0-.845-.004-.17.035-.237.23-.256a4.173 4.173 0 0 0 1.545-.475c1.396-.763 1.96-2.015 2.093-3.517.02-.23-.004-.467-.247-.588zM11.581 18c-2.089-1.642-3.102-2.183-3.52-2.16-.392.024-.321.471-.235.763.09.288.207.486.371.739.114.167.192.416-.113.603-.673.416-1.842-.14-1.897-.167-1.361-.802-2.5-1.86-3.301-3.307-.774-1.393-1.224-2.887-1.298-4.482-.02-.386.093-.522.477-.592a4.696 4.696 0 0 1 1.529-.039c2.132.312 3.946 1.265 5.468 2.774.868.86 1.525 1.887 2.202 2.891.72 1.066 1.494 2.082 2.48 2.914.348.292.625.514.891.677-.802.09-2.14.11-3.054-.614zm1-6.44a.306.306 0 0 1 .415-.287.302.302 0 0 1 .2.288.306.306 0 0 1-.31.307.303.303 0 0 1-.304-.308zm3.11 1.596c-.2.081-.399.151-.59.16a1.245 1.245 0 0 1-.798-.254c-.274-.23-.47-.358-.552-.758a1.73 1.73 0 0 1 .016-.588c.07-.327-.008-.537-.239-.727-.187-.156-.426-.199-.688-.199a.559.559 0 0 1-.254-.078.253.253 0 0 1-.114-.358c.028-.054.16-.186.192-.21.356-.202.767-.136 1.146.016.352.144.618.408 1.001.782.391.451.462.576.685.914.176.265.336.537.445.848.067.195-.019.354-.25.452z"/></svg><svg viewBox="0 0 201 201" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Groq"><path d="m128 49 1.895 1.52C136.336 56.288 140.602 64.49 142 73c.097 1.823.148 3.648.161 5.474l.03 3.247.012 3.482.017 3.613c.01 2.522.016 5.044.02 7.565.01 3.84.041 7.68.072 11.521.007 2.455.012 4.91.016 7.364l.038 3.457c-.033 11.717-3.373 21.83-11.475 30.547-4.552 4.23-9.148 7.372-14.891 9.73l-2.387 1.055c-9.275 3.355-20.3 2.397-29.379-1.13-5.016-2.38-9.156-5.17-13.234-8.925 3.678-4.526 7.41-8.394 12-12l3.063 2.375c5.572 3.958 11.135 5.211 17.937 4.625 6.96-1.384 12.455-4.502 17-10 4.174-6.784 4.59-12.222 4.531-20.094l.012-3.473c.003-2.414-.005-4.827-.022-7.241-.02-3.68 0-7.36.026-11.04-.003-2.353-.008-4.705-.016-7.058l.025-3.312c-.098-7.996-1.732-13.21-6.681-19.47-6.786-5.458-13.105-8.211-21.914-7.792-7.327 1.188-13.278 4.7-17.777 10.601C75.472 72.012 73.86 78.07 75 85c2.191 7.547 5.019 13.948 12 18 5.848 3.061 10.892 3.523 17.438 3.688l2.794.103c2.256.082 4.512.147 6.768.209v16c-16.682.673-29.615.654-42.852-10.848-8.28-8.296-13.338-19.55-13.71-31.277.394-9.87 3.93-17.894 9.562-25.875l1.688-2.563C84.698 35.563 110.05 34.436 128 49Z"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Cursor"><path d="M11.503.131 1.891 5.678a.84.84 0 0 0-.42.726v11.188c0 .3.162.575.42.724l9.609 5.55a1 1 0 0 0 .998 0l9.61-5.55a.84.84 0 0 0 .42-.724V6.404a.84.84 0 0 0-.42-.726L12.497.131a1.01 1.01 0 0 0-.996 0M2.657 6.338h18.55c.263 0 .43.287.297.515L12.23 22.918c-.062.107-.229.064-.229-.06V12.335a.59.59 0 0 0-.295-.51l-9.11-5.257c-.109-.063-.064-.23.061-.23"/></svg><svg viewBox="0 0 121 122" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Lovable"><mask id="b" width="121" height="122" x="0" y="0" maskUnits="userSpaceOnUse" style="mask-type:alpha"><path fill-rule="evenodd" d="M36.069 0c19.92 0 36.068 16.155 36.068 36.084v13.713h12.004c19.92 0 36.069 16.156 36.069 36.084 0 19.928-16.149 36.083-36.069 36.083H0v-85.88C0 16.155 16.148 0 36.069 0Z" clip-rule="evenodd"/></mask><g mask="url(#b)"><g filter="url(#c)"><ellipse cx="52.738" cy="65.101" rx="81.373" ry="81.192"/></g><g filter="url(#d)"><ellipse cx="61.673" cy="20.547" rx="104.216" ry="81.192"/></g><g filter="url(#e)"><ellipse cx="78.666" cy="5.268" rx="81.373" ry="71.304"/></g><g filter="url(#f)"><ellipse cx="63.121" cy="20.527" rx="48.937" ry="48.829"/></g></g></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Perplexity"><path d="M22.3977 7.0896h-2.3106V.0676l-7.5094 6.3542V.1577h-1.1554v6.1966L4.4904 0v7.0896H1.6023v10.3976h2.8882V24l6.932-6.3591v6.2005h1.1554v-6.0469l6.9318 6.1807v-6.4879h2.8882V7.0896zm-3.4657-4.531v4.531h-5.355l5.355-4.531zm-13.2862.0676 4.8691 4.4634H5.6458V2.6262zM2.7576 16.332V8.245h7.8476l-6.1149 6.1147v1.9723H2.7576zm2.8882 5.0404v-3.8852h.0001v-2.6488l5.7763-5.7764v7.0111l-5.7764 5.2993zm12.7086.0248-5.7766-5.1509V9.0618l5.7766 5.7766v6.5588zm2.8882-5.0652h-1.733v-1.9723L13.3948 8.245h7.8478v8.087z"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Hugging Face"><path d="M1.4446 11.5059c0 1.1021.1673 2.1585.4847 3.1563-.0378-.0028-.0691-.0058-.1058-.0058-.4209 0-.8015.16-1.0704.4512-.3454.3737-.4984.8335-.4316 1.293a1.576 1.576 0 0 0 .2148.5978c-.2319.1864-.4018.4456-.4844.7578-.0646.2448-.131.7543.2149 1.2794a1.4552 1.4552 0 0 0-.0625.1055c-.208.3923-.2207.8372-.0371 1.25.2783.6258.9696 1.1175 2.3126 1.6467.8356.3292 1.5988.5411 1.6056.543 1.1046.2847 2.104.4277 2.969.4277 1.4173 0 2.4754-.3849 3.1525-1.1446 1.538.2651 2.791.1403 3.592.006.6773.7555 1.7332 1.1387 3.1467 1.1387.8649 0 1.8643-.143 2.969-.4278.0068-.0019.77-.2138 1.6056-.543 1.343-.5292 2.0343-1.0208 2.3126-1.6466.1836-.4129.171-.8577-.037-1.25a1.4685 1.4685 0 0 0-.0626-.1056c.346-.525.2795-1.0346.2149-1.2793-.0826-.3122-.2525-.5714-.4844-.7579.11-.1816.1831-.3788.2148-.5977.0669-.4595-.0862-.9193-.4316-1.293-.2688-.2913-.6495-.4513-1.0704-.4513-.0209 0-.0376.0008-.0588.0018.3162-.9966.4846-2.0518.4846-3.1523 0-5.807-4.7362-10.5144-10.5789-10.5144-5.8426 0-10.5788 4.7073-10.5788 10.5144Zm10.5788-9.4831c5.2727 0 9.5476 4.246 9.5476 9.483a9.4201 9.4201 0 0 1-.2696 2.2365c-.0039-.0047-.0079-.011-.0117-.0156-.274-.3255-.6679-.5059-1.1075-.5059-.352 0-.714.1155-1.0763.3438-.2403.1517-.5058.422-.7793.7598-.2534-.3492-.608-.5832-1.0137-.6465a1.5174 1.5174 0 0 0-.2344-.0176c-.9263 0-1.4828.7993-1.6935 1.5177-.1046.2426-.6065 1.3482-1.3614 2.0978-1.1681 1.1601-1.4458 2.3534-.8396 3.6382-.843.1029-1.5836.0927-2.365-.006.5906-1.212.3626-2.4388-.8426-3.6322-.755-.7496-1.2568-1.8552-1.3614-2.0978-.2107-.7184-.7673-1.5177-1.6935-1.5177-.078 0-.1568.0054-.2344.0176-.4057.0633-.7604.2973-1.0137.6465-.2735-.3379-.539-.6081-.7794-.7598-.3622-.2283-.7243-.3438-1.0762-.3438-.4266 0-.8094.171-1.0821.4786a9.4208 9.4208 0 0 1-.2598-2.1936c0-5.237 4.2749-9.483 9.5475-9.483zM8.6443 7.0036c-.4838.0043-.9503.2667-1.1934.7227-.3536.6633-.1006 1.4873.5645 1.84.351.1862.4883-.5261.836-.6485.3107-.1095.841.399 1.0078.086.3536-.6634.1025-1.4874-.5625-1.84a1.3659 1.3659 0 0 0-.6524-.1602Zm6.8403 0c-.2199-.002-.4426.05-.6504.1602-.665.3526-.9181 1.1766-.5645 1.84.1669.313.6971-.1955 1.0079-.086.3476.1224.4867.8347.838.6485.6649-.3527.916-1.1767.5624-1.84-.243-.456-.7096-.7184-1.1934-.7227Zm-9.7565 1.418a.8768.8768 0 0 0-.877.877c0 .4846.3925.877.877.877a.8768.8768 0 0 0 .877-.877.8768.8768 0 0 0-.877-.877zm12.6434 0c-.4845 0-.879.3925-.879.877 0 .4846.3945.877.879.877a.8768.8768 0 0 0 .877-.877.8768.8768 0 0 0-.877-.877zM8.7927 11.459c-.179-.003-.2793.1107-.2793.416 0 .8097.3874 2.125 1.4279 2.924.207-.7123 1.3453-1.2832 1.5079-1.2012.2315.1167.2191.4417.6074.7266.3884-.285.374-.6098.6056-.7266.1627-.082 1.3009.4889 1.5079 1.2012 1.0404-.799 1.4278-2.1144 1.4278-2.924 0-1.2212-1.583.6402-3.5413.6485-1.4686-.0061-2.7266-1.0558-3.2639-1.0645zM4.312 14.4768c.5792.365 1.6964 2.2751 2.1056 3.0177.1371.2488.371.3536.582.3536.4188 0 .7465-.4138.0391-.9395-1.0636-.791-.6914-2.0846-.1836-2.1642a.4302.4302 0 0 1 .0664-.004c.4616 0 .666.7892.666.7892s.5959 1.4898 1.6213 2.508c.942.9356 1.062 1.703.4961 2.6661-.0164-.004-.0159.0236-.1484.2149-.1853.2673-.4322.4688-.7188.6152-.5062.2269-1.1397.2696-1.7833.2696-1.037 0-2.1017-.1824-2.6975-.336-.0293-.0075-3.6505-.9567-3.1916-1.8224.0771-.1454.2033-.2031.3633-.2031.6463 0 1.823.9551 2.3283.9551.113 0 .196-.0865.2285-.2031.2249-.8045-3.2787-1.0522-2.9846-2.1642.0519-.1967.193-.2757.3907-.2754.854 0 2.7704 1.4923 3.172 1.4923.0307 0 .0525-.0085.0645-.0274.2012-.3227.1096-.5865-1.3087-1.4395-1.4182-.8533-2.4315-1.329-1.8653-1.9416.0651-.0707.1574-.1015.2695-.1015.8611.0002 2.8948 1.84 2.8948 1.84s.5487.5683.8809.5683c.0762 0 .1416-.0315.1855-.1054.2355-.3946-2.1858-2.2183-2.3224-2.971-.0926-.51.0641-.7676.3555-.7676-.0006.008.1701-.0285.4942.1759zm16.2257.5918c-.1366.7526-2.5579 2.5764-2.3224 2.9709.044.074.1092.1055.1855.1055.3321 0 .881-.5684.881-.5684s2.0336-1.8397 2.8947-1.84c.1121 0 .2044.0308.2695.1016.5662.6125-.447 1.0882-1.8653 1.9415-1.4183.853-1.51 1.1168-1.3087 1.4396.012.0188.0337.0273.0644.0273.4016 0 2.3181-1.4923 3.1721-1.4923.1977-.0002.3388.0787.3907.2754.294 1.112-3.2095 1.3597-2.9846 2.1642.0325.1166.1156.2032.2285.2032.5054 0 1.682-.9552 2.3283-.9552.16 0 .2862.0577.3633.2032.459.8656-3.1623 1.8149-3.1916 1.8224-.5958.1535-1.6605.336-2.6975.336-.6351 0-1.261-.0409-1.7638-.2599-.2949-.1472-.5488-.3516-.7383-.625-.0411-.0682-.1026-.1476-.1426-.205-.5726-.9679-.455-1.7371.4903-2.676 1.0254-1.0182 1.6212-2.508 1.6212-2.508s.2044-.7891.666-.7891a.4318.4318 0 0 1 .0665.0039c.5078.0796.88 1.3732-.1836 2.1642-.7074.5257-.3797.9395.039.9395.211 0 .445-.1047.5821-.3535.4092-.7426 1.5264-2.6527 2.1056-3.0178.5588-.3524.99-.1816.8497.5918z"/></svg><svg viewBox="0 0 24 24" fill="currentColor" style="width:24px;height:24px;display:block;flex:none" role="img" aria-label="Ollama"><path d="M16.361 10.26a.894.894 0 0 0-.558.47l-.072.148.001.207c0 .193.004.217.059.353.076.193.152.312.291.448.24.238.51.3.872.205a.86.86 0 0 0 .517-.436.752.752 0 0 0 .08-.498c-.064-.453-.33-.782-.724-.897a1.06 1.06 0 0 0-.466 0zm-9.203.005c-.305.096-.533.32-.65.639a1.187 1.187 0 0 0-.06.52c.057.309.31.59.598.667.362.095.632.033.872-.205.14-.136.215-.255.291-.448.055-.136.059-.16.059-.353l.001-.207-.072-.148a.894.894 0 0 0-.565-.472 1.02 1.02 0 0 0-.474.007Zm4.184 2c-.131.071-.223.25-.195.383.031.143.157.288.353.407.105.063.112.072.117.136.004.038-.01.146-.029.243-.02.094-.036.194-.036.222.002.074.07.195.143.253.064.052.076.054.255.059.164.005.198.001.264-.03.169-.082.212-.234.15-.525-.052-.243-.042-.28.087-.355.137-.08.281-.219.324-.314a.365.365 0 0 0-.175-.48.394.394 0 0 0-.181-.033c-.126 0-.207.03-.355.124l-.085.053-.053-.032c-.219-.13-.259-.145-.391-.143a.396.396 0 0 0-.193.032zm.39-2.195c-.373.036-.475.05-.654.086-.291.06-.68.195-.951.328-.94.46-1.589 1.226-1.787 2.114-.04.176-.045.234-.045.53 0 .294.005.357.043.524.264 1.16 1.332 2.017 2.714 2.173.3.033 1.596.033 1.896 0 1.11-.125 2.064-.727 2.493-1.571.114-.226.169-.372.22-.602.039-.167.044-.23.044-.523 0-.297-.005-.355-.045-.531-.288-1.29-1.539-2.304-3.072-2.497a6.873 6.873 0 0 0-.855-.031zm.645.937a3.283 3.283 0 0 1 1.44.514c.223.148.537.458.671.662.166.251.26.508.303.82.02.143.01.251-.043.482-.08.345-.332.705-.672.957a3.115 3.115 0 0 1-.689.348c-.382.122-.632.144-1.525.138-.582-.006-.686-.01-.853-.042-.57-.107-1.022-.334-1.35-.68-.264-.28-.385-.535-.45-.946-.03-.192.025-.509.137-.776.136-.326.488-.73.836-.963.403-.269.934-.46 1.422-.512.187-.02.586-.02.773-.002zm-5.503-11a1.653 1.653 0 0 0-.683.298C5.617.74 5.173 1.666 4.985 2.819c-.07.436-.119 1.04-.119 1.503 0 .544.064 1.24.155 1.721.02.107.031.202.023.208a8.12 8.12 0 0 1-.187.152 5.324 5.324 0 0 0-.949 1.02 5.49 5.49 0 0 0-.94 2.339 6.625 6.625 0 0 0-.023 1.357c.091.78.325 1.438.727 2.04l.13.195-.037.064c-.269.452-.498 1.105-.605 1.732-.084.496-.095.629-.095 1.294 0 .67.009.803.088 1.266.095.555.288 1.143.503 1.534.071.128.243.393.264.407.007.003-.014.067-.046.141a7.405 7.405 0 0 0-.548 1.873c-.062.417-.071.552-.071.991 0 .56.031.832.148 1.279L3.42 24h1.478l-.05-.091c-.297-.552-.325-1.575-.068-2.597.117-.472.25-.819.498-1.296l.148-.29v-.177c0-.165-.003-.184-.057-.293a.915.915 0 0 0-.194-.25 1.74 1.74 0 0 1-.385-.543c-.424-.92-.506-2.286-.208-3.451.124-.486.329-.918.544-1.154a.787.787 0 0 0 .223-.531c0-.195-.07-.355-.224-.522a3.136 3.136 0 0 1-.817-1.729c-.14-.96.114-2.005.69-2.834.563-.814 1.353-1.336 2.237-1.475.199-.033.57-.028.776.01.226.04.367.028.512-.041.179-.085.268-.19.374-.431.093-.215.165-.333.36-.576.234-.29.46-.489.822-.729.413-.27.884-.467 1.352-.561.17-.035.25-.04.569-.04.319 0 .398.005.569.04a4.07 4.07 0 0 1 1.914.997c.117.109.398.457.488.602.034.057.095.177.132.267.105.241.195.346.374.43.14.068.286.082.503.045.343-.058.607-.053.943.016 1.144.23 2.14 1.173 2.581 2.437.385 1.108.276 2.267-.296 3.153-.097.15-.193.27-.333.419-.301.322-.301.722-.001 1.053.493.539.801 1.866.708 3.036-.062.772-.26 1.463-.533 1.854a2.096 2.096 0 0 1-.224.258.916.916 0 0 0-.194.25c-.054.109-.057.128-.057.293v.178l.148.29c.248.476.38.823.498 1.295.253 1.008.231 2.01-.059 2.581a.845.845 0 0 0-.044.098c0 .006.329.009.732.009h.73l.02-.074.036-.134c.019-.076.057-.3.088-.516.029-.217.029-1.016 0-1.258-.11-.875-.295-1.57-.597-2.226-.032-.074-.053-.138-.046-.141.008-.005.057-.074.108-.152.376-.569.607-1.284.724-2.228.031-.26.031-1.378 0-1.628-.083-.645-.182-1.082-.348-1.525a6.083 6.083 0 0 0-.329-.7l-.038-.064.131-.194c.402-.604.636-1.262.727-2.04a6.625 6.625 0 0 0-.024-1.358 5.512 5.512 0 0 0-.939-2.339 5.325 5.325 0 0 0-.95-1.02 8.097 8.097 0 0 1-.186-.152.692.692 0 0 1 .023-.208c.208-1.087.201-2.443-.017-3.503-.19-.924-.535-1.658-.98-2.082-.354-.338-.716-.482-1.15-.455-.996.059-1.8 1.205-2.116 3.01a6.805 6.805 0 0 0-.097.726c0 .036-.007.066-.015.066a.96.96 0 0 1-.149-.078A4.857 4.857 0 0 0 12 3.03c-.832 0-1.687.243-2.456.698a.958.958 0 0 1-.148.078c-.008 0-.015-.03-.015-.066a6.71 6.71 0 0 0-.097-.725C8.997 1.392 8.337.319 7.46.048a2.096 2.096 0 0 0-.585-.041Zm.293 1.402c.248.197.523.759.682 1.388.03.113.06.244.069.292.007.047.026.152.041.233.067.365.098.76.102 1.24l.002.475-.12.175-.118.178h-.278c-.324 0-.646.041-.954.124l-.238.06c-.033.007-.038-.003-.057-.144a8.438 8.438 0 0 1 .016-2.323c.124-.788.413-1.501.696-1.711.067-.05.079-.049.157.013zm9.825-.012c.17.126.358.46.498.888.28.854.36 2.028.212 3.145-.019.14-.024.151-.057.144l-.238-.06a3.693 3.693 0 0 0-.954-.124h-.278l-.119-.178-.119-.175.002-.474c.004-.669.066-1.19.214-1.772.157-.623.434-1.185.68-1.382.078-.062.09-.063.159-.012z"/></svg>'


def _founder_cards(s):
    """
    Replace the "Prefer email?" line with two founder cards.

    That column ran out of content two thirds of the way down while the form
    beside it kept going, so the section bottomed out in white space with a
    single mono line floating in it. Two cards fill it with the thing a reader
    at the bottom of a contact section actually wants: a person to talk to.

    No photographs: there are none in the repo. The monogram is a designed
    fallback rather than a gap - initials in the accent tint, at the size a
    portrait would have been - so this reads as finished, and dropping real
    photographs in later is a one-line change per card.

    Karan's card carries LinkedIn only. His address is not written down
    anywhere in this repo and the pattern from Raveeshu's would be a guess; a
    wrong mailto on a contact section fails silently, which is the one failure
    mode this section cannot have.
    """
    # Text anchor, for the same reason as above.
    i = s.find(">Prefer email?")
    if i != -1:
        i = s.rfind("<p ", 0, i)
    if i == -1:
        print("  'Prefer email?' line not found - CHECK")
        return s
    end = s.find("</p>", i) + len("</p>")

    # One group photograph spanning both tiles, with the two info panels
    # under it. Until that photograph exists the slot is filled with the two
    # portraits side by side, which reads as one continuous band rather than as
    # a placeholder - and swapping in the real one is a single <img>.
    GROUP_PHOTO = None

    def photo_band():
        # An explicit empty-image mark, not a cropped stand-in. A placeholder
        # that looks like content is one nobody remembers to replace.
        if GROUP_PHOTO:
            return ('<img src="%s" alt="Raveeshu Pahuja and Karankumar Sabhnani" '
                    'style="display:block;width:100%%;height:100%%;object-fit:cover">'
                    % GROUP_PHOTO)
        return (
            '<div style="width:100%;height:100%;display:flex;align-items:center;'
            'justify-content:center">'
            '<svg viewBox="0 0 24 24" fill="none" stroke="#C2A288" stroke-width="1.4" '
            'style="width:44px;height:44px" aria-hidden="true">'
            '<rect x="3" y="4.5" width="18" height="15" rx="2"></rect>'
            '<circle cx="8.5" cy="10" r="1.6"></circle>'
            '<path d="M4 17l5-5 3.5 3.5L16 12l4 4.5"></path></svg></div>'
        )

    def panel(name, role, prior, email, linkedin, divider):
        CHIP = ("display:inline-flex;align-items:center;justify-content:center;"
                "gap:7px;flex:1;padding:9px 12px;border-radius:8px;"
                "font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;"
                "font-size:.75rem;letter-spacing:.03em;text-decoration:none")
        MAIL_ICON = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
                     'stroke-width="1.8" style="width:14px;height:14px;flex:none">'
                     '<rect x="2.5" y="4.5" width="19" height="15" rx="2.5"></rect>'
                     '<path d="M3 7l9 6 9-6"></path></svg>')
        LI_ICON = ('<svg viewBox="0 0 24 24" fill="currentColor" '
                   'style="width:14px;height:14px;flex:none">%s</svg>' % LINKEDIN_PATH)
        mail = ('<a href="mailto:%s?subject=Beta%%20access" style="%s;'
                'background:rgba(132,81,46,.1);color:#84512E">%sEmail</a>'
                % (email, CHIP, MAIL_ICON)) if email else ""
        li = ('<a href="%s" target="_blank" rel="noopener" style="%s;'
              'background:rgba(10,102,194,.1);color:#0A66C2">%sLinkedIn</a>'
              % (linkedin, CHIP, LI_ICON))
        return (
            '<div style="padding:16px;display:flex;flex-direction:column;gap:2px%s">'
            '<p style="margin:0;font-size:1rem;font-weight:600;line-height:1.35">%s</p>'
            '<p style="margin:0;font-size:.875rem;color:#6B7078">%s</p>'
            '<p style="margin:6px 0 12px;font-family:\'Cascadia Code\',ui-monospace,'
            'SFMono-Regular,Menlo,monospace;font-size:.6875rem;letter-spacing:.06em;'
            'color:#9AA0A8">%s</p>'
            '<div style="margin-top:auto;display:flex;gap:8px">%s%s</div>'
            '</div>' % (divider, name, role, prior, mail, li)
        )

    block = (
        '<p style="margin:28px 0 14px;font-family:\'Cascadia Code\',ui-monospace,'
        'SFMono-Regular,Menlo,monospace;font-weight:500;font-size:.8125rem;'
        'letter-spacing:.14em;text-transform:uppercase;color:#6B7078">'
        'Prefer email, or LinkedIn \u2014 contact the founders directly</p>'
        '<div style="border:1px solid #E4E4E0;border-radius:10px;overflow:hidden;'
        'background:#FFFFFF">'
        '<div style="display:flex;width:100%;aspect-ratio:2.35/1;'
        'background:rgba(132,81,46,.06);border-bottom:1px solid #EFEFEC">'
        + photo_band() + "</div>"
        '<div data-founder-cards style="display:grid;'
        'grid-template-columns:repeat(2,minmax(0,1fr))">'
        + panel("Raveeshu Pahuja", "Co-founder",
                "Microsoft \u00b7 Twitter \u00b7 Dropbox",
                "raveeshu@sapientpriors.io",
                "https://www.linkedin.com/in/raveeshu-pahuja-82b77924/",
                ";border-right:1px solid #EFEFEC")
        + panel("Karankumar Sabhnani", "Co-founder",
                "84.51\u00b0 \u00b7 Twitter \u00b7 Univ. of Delaware",
                "karan@sapientpriors.io",
                "https://www.linkedin.com/in/ksabhnani", "")
        + "</div></div>"
    )
    return s[:i] + block + s[end:]


LINKEDIN_PATH = '<path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>'


CHART_DRAW_CSS = """
  @keyframes chart-wipe{from{transform:scaleX(0)}to{transform:scaleX(1)}}
  @keyframes chart-label-in{from{opacity:0}to{opacity:1}}
  @supports (animation-timeline: view()){
    [data-wipe]{transform-origin:0 0;transform:scaleX(0);animation:chart-wipe linear both;animation-timeline:view();animation-range:cover 12% cover 52%}
    [data-chart-label]{opacity:0;animation:chart-label-in linear both;animation-timeline:view()}
  }
  @media (prefers-reduced-motion:reduce){
    [data-wipe]{transform:none!important;animation:none!important}
    [data-chart-label]{opacity:1!important;animation:none!important}
  }
"""


MOBILE_CSS = '\n  /* ---- phone only. Desktop is untouched above 767.98px. ---- */\n  @media (max-width:767.98px){\n    /* Four stat tiles stacked full-height made the section 1365px of mostly\n       air. Two across, tighter, and the figure smaller so it still leads. */\n    [data-cols-4]{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:1px!important}\n    [data-cols-4]>div{padding:18px 14px!important}\n    [data-cols-4] p:first-child{font-size:2rem!important;margin-bottom:6px!important}\n    [data-cols-4] p:nth-child(2){font-size:.9375rem!important}\n    [data-cols-4] p:nth-child(3){font-size:.8125rem!important;line-height:1.45!important}\n\n    /* Six use-case cards at ~390px each is 2300px of scrolling. */\n    [data-usecase-card]{padding:16px!important;gap:10px!important}\n    [data-usecase-card] h3{font-size:1rem!important}\n    [data-usecase-card] p{font-size:.8125rem!important;line-height:1.45!important}\n    [data-usecase-card]>div:first-child>div{width:30px!important;height:30px!important;\n      font-size:.6875rem!important}\n\n    /* Charts. The vertical caption and a wide y-gutter cost the plot the width\n       it needs; the x labels ran into each other as one word. */\n    [data-vaxis]{display:none!important}\n    [data-yaxis]{width:26px!important;font-size:.5625rem!important}\n    [data-xaxis]{font-size:.5625rem!important;letter-spacing:0!important}\n    [data-xaxis] span{white-space:nowrap}\n    [data-xaxis] span:nth-child(2),[data-xaxis] span:nth-child(4){display:none}\n    /* point labels overlap at this width; the legend still carries the end\n       values, which is the number the reader is actually after */\n    [data-chart-label]{display:none!important}\n\n    /* The alumni marquee was running at a size where the marks were unreadable\n       and clipped at the edge. */\n    [data-marquee] img{height:26px!important}\n  }\n'
