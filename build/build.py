#!/usr/bin/env python3
"""
Turn a raw Claude Design export into the deployable site.

Run this after every re-export. Everything it does is a fix that the export
itself gets wrong, so none of it should be hand-applied to .dc.html files —
those get overwritten the next time the design is exported.

    python3 build/build.py ~/Downloads/SapientPriors-website2

Requires cwebp and ffmpeg (brew install webp ffmpeg).
"""
import os, re, shutil, subprocess, sys, glob

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# name -> (target width, quality). Chosen from the size each asset is actually
# drawn at, doubled for retina — not from the source resolution.
IMAGES = {
    "goldfish-loop":   (1400, 80),
    "goldfish-school": (1600, 80),
    "bubbles":         (1600, 80),
    "loop-pg":         (1000, 80),
    "loop-wp":         (1000, 80),
    "motes-pg":        (1200, 78),
}
# Already shipped as good WebP by the export; copied through untouched.
PASSTHROUGH = ["strata.webp", "cards.webp"]

# Every .png reference the pages must be repointed to its .webp.
REWRITES = {f"art/{n}.png": f"art/{n}.webp" for n in IMAGES}
REWRITES.update({"art/strata.png": "art/strata.webp", "art/cards.png": "art/cards.webp"})

# Mono goes to Cascadia Code everywhere it is used - code samples, the API docs
# blocks, section kickers, axis ticks and figures. Done as a rewrite rather
# than a patch because the family name appears in every page and in both
# standalone scripts, and a per-file patch would leave whichever file was added
# next still asking for a font the site no longer ships.
#
# The variable file carries the same 400-700 axis the old one did, so no
# weight declaration changes. It costs 48.6KB against JetBrains' 31KB.
REWRITES.update({
    "@font-face{font-family:'JetBrains Mono';font-style:normal;font-weight:400 700;"
    "font-display:swap;src:url('fonts/jetbrains-mono-var-latin.woff2') format('woff2')}":
    "@font-face{font-family:'Cascadia Code';font-style:normal;font-weight:400 700;"
    "font-display:swap;src:url('fonts/cascadia-code-var-latin.woff2') format('woff2')}",
    "'JetBrains Mono',monospace": "'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace",
    "'JetBrains Mono', monospace": "'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace",
    # Hero Motion.dc.html still asks Google for JetBrains. Cascadia is not on
    # Google Fonts and the page's CSS now names Cascadia anyway, so the request
    # only costs a round trip to fetch a face nothing references.
    "&family=JetBrains+Mono:wght@400;500": "",
})

HASH_FIX = """<script>
/* The page hydrates after parse, so the browser resolves location.hash before
   the section ids exist, finds nothing, and never retries — every anchor link
   lands at the top. Re-apply the hash once the target appears. */
(function () {
  var id = location.hash ? location.hash.slice(1) : "";
  if (!id) return;
  var tries = 0;
  (function go() {
    var el = document.getElementById(id);
    if (el) { el.scrollIntoView(); return; }
    if (tries++ < 90) requestAnimationFrame(go);
  })();
})();
</script>
"""

TRY_DEMO = '<script src="try-demo.js" defer></script>\n'
CHART_SCROLL = '<script src="chart-scroll.js" defer></script>\n'


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"failed: {' '.join(cmd)}\n{r.stderr[:400]}")


def kb(p):
    return os.path.getsize(p) / 1024


def main(src):
    src = os.path.expanduser(src)
    if not os.path.isdir(src):
        raise SystemExit(f"no such export directory: {src}")

    out = HERE
    art_out = os.path.join(out, "art")
    os.makedirs(art_out, exist_ok=True)

    # 1. Pages and small assets straight through. uploads/ is deliberately not
    #    copied: it is ~50MB of duplicates that no page references.
    for d in ("fonts", "logos"):
        if os.path.isdir(os.path.join(src, d)):
            shutil.copytree(os.path.join(src, d), os.path.join(out, d), dirs_exist_ok=True)
    for f in ("support.js", "image-slot.js"):
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), out)
    for f in glob.glob(os.path.join(src, "*.dc.html")):
        shutil.copy2(f, out)

    # A static host needs a root document; the export has none.
    shutil.copy2(os.path.join(src, "SapientPriors.dc.html"), os.path.join(out, "index.html"))

    # 2. Art: the export ships full-resolution PNGs, ~30MB of them.
    print("images")
    for name, (w, q) in IMAGES.items():
        s = os.path.join(src, "art", f"{name}.png")
        if not os.path.exists(s):
            print(f"  - {name}.png not in export, skipped"); continue
        d = os.path.join(art_out, f"{name}.webp")
        run(["cwebp", "-quiet", "-q", str(q), "-resize", str(w), "0",
             "-alpha_q", "90", "-m", "6", s, "-o", d])
        print(f"  {name:18s} {kb(s)/1024:6.2f} MB -> {kb(d):6.1f} KB")
    for f in PASSTHROUGH:
        s = os.path.join(src, "art", f)
        if os.path.exists(s):
            shutil.copy2(s, art_out)

    # 3. Video. The export emits H.265/HEVC, which Safari plays and Chrome and
    #    Firefox do not, so the loop is dead for most visitors. It also carries
    #    a pointless audio track on a muted element.
    # The curtain no longer plays the film, so re-encoding it each build only
    # produced a 428KB file nothing references. Left here rather than deleted
    # because the export still ships it and a future curtain may want it back.
    v_in = os.path.join(src, "art", "goldfish-swim.mp4")
    if False and os.path.exists(v_in):
        v_out = os.path.join(art_out, "goldfish-swim.mp4")
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", v_in, "-an",
             "-vf", "scale=1280:-2", "-c:v", "libx264", "-profile:v", "main",
             "-pix_fmt", "yuv420p", "-crf", "27", "-preset", "slow",
             "-movflags", "+faststart", v_out])
        print(f"video\n  goldfish-swim      {kb(v_in)/1024:6.2f} MB -> {kb(v_out):6.1f} KB  (hevc -> h264)")

    # 4. Page rewrites.
    print("pages")
    for p in glob.glob(os.path.join(out, "*.html")):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        n = 0
        for a, b in REWRITES.items():
            n += s.count(a); s = s.replace(a, b)
        # a 5s muted background loop does not need the whole file before paint
        s = s.replace('preload="auto"', 'preload="metadata"')

        i = s.rfind("</body>")
        add = HASH_FIX + (TRY_DEMO if os.path.basename(p) == "TryIt.dc.html" else "")
        if os.path.basename(p) in ("SapientPriors.dc.html", "index.html"):
            add += CHART_SCROLL
        if "Deploy-time fix" not in s and "hash ? location.hash" not in s:
            s = (s[:i] + add + s[i:]) if i != -1 else (s + add)

        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        if n:
            print(f"  {os.path.basename(p):28s} {n} asset refs repointed")

    # 5. Nav dropdown: the panel sits 6px below the trigger with nothing
    #    hoverable in between, so the menu closes when you reach for it.
    nav = os.path.join(out, "SiteNav.dc.html")
    if os.path.exists(nav):
        s = open(nav, encoding="utf-8", errors="surrogateescape").read()
        old = ('<div style="position:absolute;left:0;top:calc(100% + 6px);z-index:60;width:20rem;'
               'padding:8px;border-radius:12px;border:1px solid #E4E4E0;background:#FFFFFF;'
               'box-shadow:0 12px 32px -12px rgba(20,22,26,.18)">')
        if old in s:
            new = ('<div style="position:absolute;left:0;top:100%;z-index:60;padding-top:6px">'
                   '<div style="width:20rem;padding:8px;border-radius:12px;border:1px solid #E4E4E0;'
                   'background:#FFFFFF;box-shadow:0 12px 32px -12px rgba(20,22,26,.18)">')
            i = s.index(old)
            s = s[:i] + new + s[i + len(old):]
            j = s.index("</sc-if>", i)
            s = s[:j] + "</div>" + s[j:]
            open(nav, "w", encoding="utf-8", errors="surrogateescape").write(s)
            print("  SiteNav.dc.html              dropdown hover bridge applied")
        else:
            print("  SiteNav.dc.html              dropdown already patched or markup changed — CHECK")

    patch_tryit(out)
    patch_under_construction(out)
    sys.path.insert(0, os.path.join(HERE, 'build'))
    import patch_contact
    patch_contact.apply(out)
    patch_contact.apply_success_state(out)
    patch_contact.unify_tryit_form(out)
    patch_contact.shorten(out)
    patch_contact.founder_photo(out)
    import patch_content
    print('content')
    patch_content.apply(out)
    import patch_ui
    print('ui')
    patch_ui.apply(out)
    import patch_nav_copy
    print('nav + copy')
    patch_nav_copy.apply(out)

    import patch_address
    print('address')
    patch_address.apply(out)

    import patch_copyright
    print('copyright')
    patch_copyright.apply(out)

    import patch_api_demo
    print('api demo')
    patch_api_demo.apply(out)

    import patch_copy
    print('copy')
    patch_copy.apply(out)

    import patch_urls
    print('urls')
    patch_urls.apply(out)

    import patch_head
    print('head')
    patch_head.apply(out)

    import patch_motion
    print('motion')
    patch_motion.apply(out)


    # 6. Report and verify.
    total = sum(os.path.getsize(os.path.join(r, f))
                for r, d, fs in os.walk(out) if ".git" not in r for f in fs)
    print(f"\ntotal: {total/1048576:.2f} MB")

    missing = set()
    pat = re.compile(r'''(?:src|href|poster)\s*=\s*["']([^"']+)["']|url\((["']?)([^)"']+)\2\)''')
    import urllib.parse
    for p in glob.glob(os.path.join(out, "*.html")):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        for m in pat.finditer(s):
            ref = (m.group(1) or m.group(3) or "").strip()
            if not ref or ref.startswith(("data:", "#", "javascript:", "mailto:", "tel:", "http", "//", "{{")):
                continue
            path = urllib.parse.unquote(ref.split("?")[0].split("#")[0]).lstrip("/")
            if not os.path.exists(os.path.join(out, path)):
                missing.add(path)
    print("missing assets:", sorted(missing) or "none")




def patch_under_construction(out):
    """
    Put the site's own illustration on the three "still being built" pages.

    The export gives each of them a different faint background — the loop, the
    strata, the cards — at opacity .62 behind a brightness/contrast filter
    tuned for background texture. On these pages the art is not background: it
    is the only thing on the right-hand half, and it is what makes an empty
    page feel deliberate instead of broken. So all three get the same
    illustration, at full strength, without the wash.
    """
    import re, glob
    art = "art/under-construction.webp"
    if not os.path.exists(os.path.join(out, art)):
        print("  under-construction art missing — run build/prepare-illustration.py")
        return
    n = 0
    for p in glob.glob(os.path.join(out, "*.dc.html")):
        s = open(p, encoding="utf-8", errors="surrogateescape").read()
        m = re.search(r'<div data-uc-art[^>]*>', s)
        if not m:
            continue
        tag = m.group(0)
        new = re.sub(r"background:url\('art/[^']+'\)", f"background:url('{art}')", tag)
        new = new.replace("filter:brightness(1.12) contrast(1.34) saturate(.9);", "")
        new = new.replace("opacity:.62;", "opacity:.94;")
        if new != tag:
            s = s.replace(tag, new)
            open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
            n += 1
    if n:
        print(f"under construction\n  illustration applied to {n} pages")

def patch_tryit(out):
    """
    Turn the Try It waitlist into an enterprise contact section.

    Three separate problems, all of which the export reintroduces:

    1. Two decorative art blocks sat in this page at a scale that did not match
       anything around them, so they read as filler rather than design.
    2. The section was framed as a personal waitlist ("put your name down",
       "move up the queue") when the audience is companies. The steps content
       already described a working session; only the framing was wrong.
    3. The form threw every submission away. The handler was
       `e.preventDefault(); setState({sent:true})` — no fetch, no action, no
       mailto. It said "You are on the list" and nothing left the browser.
    """
    import re
    p = os.path.join(out, "TryIt.dc.html")
    if not os.path.exists(p):
        return
    s = open(p, encoding="utf-8", errors="surrogateescape").read()
    before = s
    notes = []

    # 1. Drop the two decorative art blocks on this page only.
    s, n = re.subn(
        r'<div data-section-art aria-hidden="true"[^>]*?(?:goldfish-loop|bubbles)[^>]*?></div>',
        "", s)
    if n: notes.append(f"removed {n} decorative art blocks")

    # 2. Reframe waitlist -> enterprise contact.
    COPY = [
        (">The waitlist<", ">Talk to us<"),
        (">Tell us what keeps forgetting.<",
         ">Your first memory call is 30 minutes away.<"),
        ("One line is enough. We read every one of these, and the specific ones move up "
         "the queue \u2014 a real assistant with a real memory problem is worth more to us "
         "than a job title.",
         "Bring one assistant that keeps forgetting and we will wire the memory layer "
         "into it on the call. You leave with API access and a before-and-after you can "
         "show your team."),
        ("The API is in private beta.", "Built for teams running assistants in production."),
        ("We're onboarding a handful of teams at a time so each one gets a real working "
         "session rather than a key and a docs link. Put your name down and we'll come "
         "back with a slot.",
         "We onboard a handful of companies at a time so each one gets a real working "
         "session rather than a key and a docs link. Tell us what keeps forgetting and "
         "we'll come back with a slot."),
        (">Join the waitlist<", ">Book a working session<"),
    ]
    for a, b in COPY:
        a = a.encode().decode("unicode_escape") if "\\u" in a else a
        if a in s:
            s = s.replace(a, b); notes.append("copy: " + a[:34])

    # 3. Company field. An enterprise contact form that does not ask which
    #    company is not an enterprise contact form.
    #
    #    Cloned from the live email field rather than hand-written, so it keeps
    #    whatever styling the export currently uses instead of freezing a copy
    #    of it that silently drifts.
    if "ti-company" not in s:
        e = s.find('for="ti-email"')
        w = s.rfind("<div", 0, e)                       # the field wrapper
        close = s.find("</div>", s.find("id=\"ti-email\""))
        if e != -1 and w != -1 and close != -1:
            block = s[w:close + len("</div>")]
            company = (block
                       .replace("ti-email", "ti-company")
                       .replace(">Work email *<", ">Company *<")
                       .replace('type="email" ', "")
                       .replace('placeholder="jordan@company.com"', 'placeholder="Acme Inc."')
                       .replace("{{ fEmail }}", "{{ fCompany }}")
                       .replace("{{ setEmail }}", "{{ setCompany }}"))
            k = s.find('for="ti-what"')
            wk = s.rfind("<div", 0, k)
            if wk != -1:
                s = s[:wk] + company + "\n              " + s[wk:]
                notes.append("added Company field")

    # 4. Component state + bindings for the new field.
    s = s.replace("state = { name: '', email: '', what: '', model: '', size: null, sent: false };",
                  "state = { name: '', email: '', company: '', what: '', model: '', size: null, sent: false };")
    s = s.replace("      fName: s.name,", "      fCompany: s.company,\n      fName: s.name,")
    s = s.replace("      setName: this.field('name'),",
                  "      setCompany: this.field('company'),\n      setName: this.field('name'),")

    # 5. Make the form deliver. There is no backend on a static host, so this
    #    hands the lead to the visitor's mail client with everything filled in.
    #    Stopgap, not a destination: swap for a real endpoint when one exists.
    old_submit = "      submit: e => { e.preventDefault(); this.setState({ sent: true }); },"
    new_submit = (
        "      submit: e => {\n"
        "        e.preventDefault();\n"
        "        const lines = [\n"
        "          'Name: ' + s.name,\n"
        "          'Work email: ' + s.email,\n"
        "          'Company: ' + s.company,\n"
        "          'What keeps forgetting: ' + s.what,\n"
        "          'Rough user count: ' + (s.size || 'not given'),\n"
        "          'Model in use: ' + (s.model || 'not given')\n"
        "        ].join('\\n');\n"
        "        window.location.href = 'mailto:contact@sapientpriors.com'\n"
        "          + '?subject=' + encodeURIComponent('Working session \u2014 ' + (s.company || s.name))\n"
        "          + '&body=' + encodeURIComponent(lines);\n"
        "        this.setState({ sent: true });\n"
        "      },"
    )
    if old_submit in s:
        s = s.replace(old_submit, new_submit); notes.append("submit now sends a prefilled mail")

    s = s.replace("submitLabel: s.sent ? 'You are on the list' : 'Join the waitlist',",
                  "submitLabel: s.sent ? 'Opening your mail client' : 'Book a working session',")
    s = s.replace("? 'We have it. Expect a reply from a person, not a sequence.'",
                  "? 'Your mail client should have opened with the details filled in. Send it and we reply within a week.'")
    s = s.replace("        : 'We reply to every one of these ourselves. Usually within a week.'",
                  "        : 'Goes straight to a founder. We reply to every one of these ourselves, usually within a week.'")

    if s != before:
        open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
        print("try it")
        for n in notes:
            print("  " + n)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "~/Downloads/SapientPriors-website2")
