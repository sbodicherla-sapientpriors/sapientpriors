"""
Content corrections applied after every export.

Four changes, each of which the design source will reintroduce until it is
edited there too.
"""
import os
import re


def _matching_div_end(s, start):
    """Index just past the </div> that closes the <div> opening at `start`."""
    depth, i = 0, start
    for m in re.finditer(r"<div\b[^>]*>|</div>", s[start:]):
        i = start + m.end()
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0:
            return i
    return -1


BENCH_JS = """const BENCH = [
  { suite: 'LongMem', note: 'Run pending', overall: '\\u2014', single: '\\u2014', multi: '\\u2014', temporal: '\\u2014', open: '\\u2014' },
  { suite: 'BEAM', note: 'Run pending', overall: '\\u2014', single: '\\u2014', multi: '\\u2014', temporal: '\\u2014', open: '\\u2014' },
  { suite: 'LoCoMo', note: 'Complete', overall: '91.6', single: '92.3', multi: '93.3', temporal: '92.8', open: '76.0' }
];

"""

TH = ("padding:12px 16px;text-align:right;font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;"
      "font-weight:500;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:#6B7078")
TH1 = TH.replace("text-align:right", "text-align:left")
TD = ("padding:13px 16px;text-align:right;font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace;"
      "font-size:.9rem;color:#14161A")
TD1 = ("padding:13px 16px;text-align:left;font-size:.9375rem;font-weight:500;color:#14161A")

TABLE = (
    '<div style="grid-column:span 8">\n'
    '              <h3 style="margin:0 0 10px;font-family:Newsreader,Georgia,serif;font-weight:400;'
    'font-size:1.5rem;letter-spacing:-.01em;color:#14161A">Suites and scores</h3>\n'
    '              <p style="margin:0 0 20px;font-size:1rem;line-height:1.6;color:#6B7078">'
    'One table, so the gaps are as legible as the numbers. A dash is a run that has not finished '
    '— left empty rather than filled with an estimate.</p>\n'
    '              <div style="overflow-x:auto;border:1px solid #E4E4E0;border-radius:12px;background:#FFFFFF">\n'
    '                <table style="width:100%;border-collapse:collapse;min-width:36rem">\n'
    '                  <thead><tr style="background:#F6F6F4;border-bottom:1px solid #E4E4E0">\n'
    '                    <th style="' + TH1 + '">Suite</th>\n'
    '                    <th style="' + TH + '">Overall</th>\n'
    '                    <th style="' + TH + '">Single hop</th>\n'
    '                    <th style="' + TH + '">Multi hop</th>\n'
    '                    <th style="' + TH + '">Temporal</th>\n'
    '                    <th style="' + TH + '">Open domain</th>\n'
    '                  </tr></thead>\n'
    '                  <tbody>\n'
    '                    <sc-for list="{{ bench }}" as="r" hint-placeholder-count="3">\n'
    '                      <tr style="border-bottom:1px solid #EFEFEC">\n'
    '                        <th scope="row" style="' + TD1 + '">{{ r.suite }}'
    '<span style="display:block;margin-top:2px;font-family:\'Cascadia Code\',ui-monospace,SFMono-Regular,Menlo,monospace;'
    'font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;color:#9AA0A8">{{ r.note }}</span></th>\n'
    '                        <td style="' + TD + '">{{ r.overall }}</td>\n'
    '                        <td style="' + TD + '">{{ r.single }}</td>\n'
    '                        <td style="' + TD + '">{{ r.multi }}</td>\n'
    '                        <td style="' + TD + '">{{ r.temporal }}</td>\n'
    '                        <td style="' + TD + '">{{ r.open }}</td>\n'
    '                      </tr>\n'
    '                    </sc-for>\n'
    '                  </tbody>\n'
    '                </table>\n'
    '              </div>\n'
    '              <p style="margin:14px 0 0;font-size:.875rem;line-height:1.6;color:#9AA0A8">'
    'Our own evaluation on the public sets, scored with an LLM-as-judge rubric. Method and prompts '
    'available on request.</p>\n'
    '            </div>'
)


def apply(out):
    for name in ("SapientPriors.dc.html", "index.html", "Team.dc.html",
                 "Research.dc.html", "SiteNav.dc.html"):
        p = os.path.join(out, name)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        before = s

        # 1. The lab headline. Nothing has been published yet, so the old line
        #    promised a track record that does not exist.
        s = s.replace("We publish what we learn.", "We show our working.")
        # The team page repeats the claim inside a sentence, and names the
        # parent company rather than the research arm.
        s = s.replace(
            "We publish what we learn, and we hire people who want their work read.",
            "We show our working, and we hire people who want their work used.")
        s = s.replace("TCS Research and Samsung R&amp;D.", "TCS Research and Samsung Research.")
        s = s.replace("TCS Research and Samsung R&D.", "TCS Research and Samsung Research.")
        s = s.replace("prior: 'Samsung R&D Institute'", "prior: 'Samsung Research'")

        # "Publish" appears twice more, and both promise a body of published
        # work that does not exist yet. Both mean "show", so both say show.
        s = s.replace("Where a number exists we publish it,", "Where a number exists we show it,")
        s = s.replace("description: 'The lab and what we publish'",
                      "description: 'The lab and how we work'")

        # 2. Alumni labels: the people came from the research arms, not the
        #    parent companies, and the wall should say which.
        # The X mark is the current company; these people worked at Twitter,
        # and the bird is what that era looked like on a CV.
        s = s.replace("{ name: 'Twitter', logo: 'logos/twitter.svg', aspect: 1, scale: 0.86 }",
                      "{ name: 'Twitter', logo: 'logos/twitter-bird.webp', "
                      "aspect: 1.23, scale: 1.0 }")

        # Real marks for the four that were set in type. The parent-company
        # logos said Samsung and TCS, which is not where these people worked;
        # these say Research. Aspect ratios come from the trimmed artwork, not
        # the source canvas, so the strip's equal-area sizing is honest.
        s = s.replace("{ name: 'Samsung R&D Institute', logo: 'logos/samsung.svg', aspect: 1, scale: 1.5 }",
                      "{ name: 'Samsung Research', logo: 'logos/samsung-research.webp', "
                      "aspect: 2.32, scale: 1.2 }")
        # TIFR replaces TCS Research. The source was a JPEG carrying a baked-in
        # transparency checkerboard, which the colour rule reads as ink - the
        # grey squares are only ~20% from white. Cleared on saturation first
        # (the checker is neutral, the mark is a saturated blue), then masked.
        s = s.replace("{ name: 'TCS Research', logo: 'logos/tcs.svg', aspect: 1, scale: 1.24 }",
                      "{ name: 'TIFR', logo: 'logos/tifr.webp', "
                      "aspect: 2.14, scale: 1.0, caption: 'Tata Institute of Fundamental Research' }")
        # IISc: replaced with the full emblem. The new artwork is portrait
        # (0.92) where the old was landscape (1.24), and the strip sizes by
        # equal optical area, so leaving the old aspect would have sized it
        # against a shape it no longer is.
        s = s.replace("{ name: 'Indian Institute of Science' }",
                      "{ name: 'Indian Institute of Science', logo: 'logos/iisc.webp', "
                      "aspect: 0.92, scale: 1.30, "
                      "caption: 'Indian Institute of Science' }")
        # Marks that do not say their own name.
        #
        # Dropbox is a box and Twitter is a bird: nothing in either drawing
        # tells a reader which company it is. Written as a pass over the built
        # string rather than as more literal replacements because these entries
        # are defined in three different places - the export, the patch above,
        # and each other - and a caption should not depend on which.
        #
        # There is no second marquee for this. A parallel track underneath would
        # have to stay in step with the one above it, and two CSS animations
        # drift: they start at different moments and nothing holds them
        # together, so the names would slide out from under their logos. Each
        # caption rides inside the same item as its mark instead, which cannot
        # drift from itself.
        # Only pages carrying the strip: most do not, and warning about a list
        # that was never on the page buries the warning that matters.
        for _nm, _cap in (("Dropbox", "Dropbox"), ("Twitter", "Twitter")) \
                if "alumniTrack" in s else ():
            _i = s.find("{ name: '%s'" % _nm)
            if _i == -1:
                print("  alumni entry %s not found - no caption - CHECK" % _nm)
                continue
            _j = s.index("}", _i)
            if "caption:" in s[_i:_j]:
                continue
            s = s[:_j] + ", caption: '%s' " % _cap + s[_j:]

        # Kroger: white script inside a solid blue ellipse. This was on the
        # rejected list for months because flattening it produced a filled
        # blob; the knockout rule keeps the lettering as holes.
        s = s.replace("{ name: 'Kroger AI' }",
                      "{ name: 'Kroger AI', logo: 'logos/kroger.webp', "
                      "aspect: 1.27, scale: 1.35 }")
        # Multi-coloured sources: converted with the colour mode, which reads
        # distance from white rather than brightness so OpenNLP's orange does
        # not come out half-faded beside its red.
        s = s.replace("{ name: 'OpenNLP Labs' }",
                      "{ name: 'OpenNLP Labs', logo: 'logos/opennlp.webp', "
                      "aspect: 2.87, scale: 1.15 }")
        s = s.replace("{ name: 'KENOME' }",
                      "{ name: 'KENOME', logo: 'logos/kenome.webp', "
                      "aspect: 3.90, scale: 1.15 }")
        s = s.replace("{ name: 'New York University' }",
                      "{ name: 'New York University', logo: 'logos/nyu.webp', "
                      "aspect: 0.70, scale: 1.05 }")

        # 3. South Park Commons was reading small against the wordmarks.
        # South Park Commons out of the alumni strip. It is an investor, and it
        # is already named in "Backed by" - in a row captioned "where the team
        # is from" it reads as a place someone worked.
        import re as _re_spc
        s = _re_spc.sub(r",?\s*\{ name: 'South Park Commons'[^}]*\}", "", s)

        # 4. One benchmark table instead of two blocks.
        if "{{ bench }}" not in s:
            i = s.find("The suites still running")
            if i != -1:
                h3 = s.rfind("<h3", 0, i)
                block = s.rfind("<div", 0, h3)
                end = _matching_div_end(s, block)
                if end != -1:
                    s = s[:block] + s[end:]

            j = s.find('<div style="grid-column:span 8">')
            if j != -1:
                end = _matching_div_end(s, j)
                if end != -1:
                    s = s[:j] + TABLE + s[end:]

            s = s.replace("const LOCOMO = [", BENCH_JS + "const LOCOMO = [")
            s = s.replace("      pending: PENDING,", "      bench: BENCH,")

        if s != before:
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            print("  " + name)
