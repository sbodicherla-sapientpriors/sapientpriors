# -*- coding: utf-8 -*-
"""
The API card in the hero: two worked exchanges, rotating.

Each card is one exchange split into two stacked sections - what the user asked,
then what the model returned with that user's context applied. Split rather than
merged because the argument only lands if you can see the second obeying the
first: the context asks for short replies and a cited source, and the reply is
short and cites its source.

Two examples on one 14s loop, a different task each: the same call, two users,
two sets of learned preferences.

Content lives in EXAMPLES and nowhere else. To swap either exchange, edit that
list - nothing below it needs touching.

No figure appears anywhere on this card. Both read "under a second", in words,
by instruction: nothing behind it is a measurement, and every number tried here
was invented to look plausible - 48ms, then 0.2s and 0.9s - each claiming a
precision the site cannot support.

  Do not substitute a figure here without being asked for one.

Rotation is CSS, not script. Both panels sit in the same grid cell, so the card
takes the height of the taller and neither is positioned absolutely. The
resting state resolves to the first panel: if the animation never runs, the two
must not print on top of each other.
"""
import glob
import io
import os

MONO = ("font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,"
        "monospace")
PUNC, KEY, STR, NUM, INK = "#9AA0A8", "#6B7078", "#3A3E45", "#84512E", "#14161A"
LINE, GREEN = "#EFEFEC", "#2E8B5A"

LATENCY = "under a second"

EXAMPLES = [
    {
        "path": "/v1/&hellip;/completions?task=email_drafting",
        "user": "u_8213",
        "query": "Can you draft an email to john",
        "context": ["prefers short replies, no preamble",
                    "john works in insurance claims",
                    "has a casual tone with john",
                    "always asks for the source"],
        "output": "Hey John — file attached. Source: the Aug 14 export.",
        "caption": "One call, before your prompt. No fine-tuning, no vector "
                   "store to run.",
    },
    {
        "path": "/v1/&hellip;/completions?task=code_review",
        "user": "u_4417",
        "query": "Add retries to the upload handler",
        "context": ["explicit error types, never a bare except",
                    "no new dependencies without asking",
                    "ships a test with every fix",
                    "prefers small diffs"],
        "output": "Bounded retry with an explicit UploadTimeout, plus a test. "
                  "No new deps.",
        "caption": "Same call, another user. The context is theirs, not a "
                   "prompt you maintain.",
    },
]

START = ('<div style="display:flex;align-items:center;justify-content:'
         'space-between;border-bottom:1px solid #EFEFEC;padding:12px 16px">')
END = "No fine-tuning, no vector store to run.</p>"

KEYFRAMES = (
    "\n  /* The two API panels, 50% out of phase on one 14s loop. Pure CSS so a"
    "\n     runtime re-render cannot leave the rotation un-armed. */"
    "\n  @keyframes api-a{0%,44%{opacity:1}50%,94%{opacity:0}100%{opacity:1}}"
    "\n  @keyframes api-b{0%,44%{opacity:0}50%,94%{opacity:1}100%{opacity:0}}\n"
)


def _sp(colour, text):
    return '<span style="color:%s">%s</span>' % (colour, text)


def _label(text, right=""):
    return (
        '<div style="display:flex;align-items:center;justify-content:'
        'space-between;padding:10px 16px 0">'
        '<span style="%s;font-size:.6875rem;letter-spacing:.14em;'
        'text-transform:uppercase;color:#9AA0A8">%s</span>%s</div>'
        % (MONO, text, right)
    )


def _pre(body):
    return ('<pre style="margin:0;overflow-x:auto;padding:8px 16px 14px;'
            'font-size:.8125rem;line-height:1.625;white-space:pre-wrap;'
            'overflow-wrap:anywhere"><code style="%s">%s'
            '</code></pre>' % (MONO, body))


def _user_block(ex):
    out = [_sp(PUNC, "{")]
    out.append('  ' + _sp(KEY, '"user"') + _sp(PUNC, ": ") +
               _sp(STR, '"%s"' % ex["user"]) + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"query"') + _sp(PUNC, ": ") +
               _sp(STR, '"%s"' % ex["query"]) + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"context"') + _sp(PUNC, ": ["))
    ctx = ex["context"]
    for n, c in enumerate(ctx):
        out.append('    ' + _sp(STR, '"%s"' % c) +
                   (_sp(PUNC, ",") if n < len(ctx) - 1 else ""))
    out.append('  ' + _sp(PUNC, "]"))
    # The closing brace carries its own newline: the runtime drops the last
    # whitespace text node in a <pre>, so a brace written as its own line lands
    # welded to the value above it. Inside the span it is text, and text stays.
    return "\n".join(out) + _sp(PUNC, "\n}")


def _output_block(ex):
    return _sp(INK, '"%s"' % ex["output"])


def _panel(anim, opacity, ex):
    status = ('<span style="%s;font-size:.6875rem;letter-spacing:.14em;'
              'text-transform:uppercase;color:%s">200 &middot; %s</span>'
              % (MONO, GREEN, LATENCY))
    head = (
        '<div style="border-bottom:1px solid %s;padding:12px 16px">'
        '<span style="%s;font-size:.9375rem;color:#6B7078">POST %s</span>'
        '</div>' % (LINE, MONO, ex["path"])
    )
    user = _label("User") + _pre(_user_block(ex))
    rule = '<div style="border-top:1px solid %s"></div>' % LINE
    model = _label("Model output", status) + _pre(_output_block(ex))
    foot = (
        '<p style="margin:0;border-top:1px solid %s;padding:12px 16px;'
        'font-size:1rem;line-height:1.6;color:#6B7078">%s</p>'
        % (LINE, ex["caption"])
    )
    # min-width:0 is load-bearing. A grid item defaults to min-width:auto, so
    # the widest <pre> line pushes the panel wider than the card that holds it
    # instead of scrolling inside its own box - measured at 61px of overhang,
    # which put the status line outside the card's right edge.
    return ('<div style="grid-area:1/1;min-width:0;opacity:%d;animation:%s 14s '
            'linear infinite">%s%s%s%s%s</div>'
            % (opacity, anim, head, user, rule, model, foot))


# Step 03 in "How it works" quotes this same call. It carried 48ms - the figure
# this card started with, and no more measured there than it was here.
STEP_FROM = "result: '200 OK · 48ms'"
STEP_TO = "result: '200 OK · under a second'"


def apply(out):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        i = s.find(START)
        if i == -1 or END not in s:
            continue
        j = s.index(END) + len(END)
        block = ('<div style="display:grid;min-width:0">'
                 + _panel("api-a", 1, EXAMPLES[0])
                 + _panel("api-b", 0, EXAMPLES[1])
                 + '</div>')
        s = s[:i] + block + s[j:]
        s = s.replace(STEP_FROM, STEP_TO)
        if "@keyframes api-a" not in s:
            s = s.replace("\n</style>", KEYFRAMES + "</style>", 1)
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  api demo rebuilt on %d pages" % n)
    if n == 0:
        print("  api demo card not found - still the old panel - CHECK")
