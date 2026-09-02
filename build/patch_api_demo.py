# -*- coding: utf-8 -*-
"""
The API card in the hero: two responses, rotating.

One panel was doing two jobs badly. It showed a context lookup but no query, so
there was nothing for the context to be the answer to, and it ended on
"learned_from: 31 conversations" - a number about us rather than about the user
being served.

Two panels now, on one 14s loop:

  1. the lookup    the query going in, and the context that comes back
  2. the answer    the same user's reply, written with that context applied

Both panels are quoted in seconds, not milliseconds. A figure like "48ms"
invites arithmetic about a single hop; the claim being made here is that the
whole thing is quick, so the numbers are given at the resolution of that
claim - 0.2s for the lookup, 0.9s for the round trip with the model in it.

Step 03 further down the page still quotes this same call at 48ms. That is a
retrieval-latency claim backing the "faster than Mem0" tile rather than a
response-time one, so it is left alone here deliberately, not by oversight.

They are written so the second visibly obeys the first: the context says short
replies with no preamble, a casual tone with John, and always cite the source,
and the reply is short, opens "Hey John", and names where the number came from.
That connection is the whole argument of the section, and one panel could not
make it.

Rotation is CSS, not script. Both panels sit in the same CSS grid cell, so the
card takes the height of the taller one and neither is positioned absolutely;
the crossfade is two keyframe tracks 50% out of phase. Nothing to re-arm when
the runtime replaces these nodes, which is the failure this codebase keeps
finding with mounted scripts.
"""
import glob
import io
import os

MONO = ("font-family:'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,"
        "monospace")
PUNC, KEY, STR, NUM = "#9AA0A8", "#6B7078", "#3A3E45", "#84512E"

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


def _panel(anim, opacity, method, path, ms, lines, caption):
    head = (
        '<div style="display:flex;align-items:center;justify-content:'
        'space-between;border-bottom:1px solid #EFEFEC;padding:12px 16px">'
        '<span style="%s;font-size:.9375rem;color:#6B7078">%s %s</span>'
        '<span style="%s;font-size:.9375rem;color:#2E8B5A">200 &middot; %s</span>'
        '</div>' % (MONO, method, path, MONO, ms)
    )
    body = (
        '<pre style="margin:0;overflow-x:auto;padding:16px;font-size:.8125rem;'
        'line-height:1.625"><code style="%s">%s</code></pre>' % (MONO, lines)
    )
    foot = (
        '<p style="margin:0;border-top:1px solid #EFEFEC;padding:12px 16px;'
        'font-size:1rem;line-height:1.6;color:#6B7078">%s</p>' % caption
    )
    # The inline opacity is the resting state, and it matters: two panels share
    # one grid cell, so if the animation never runs - reduced motion, an old
    # engine, anything - the overlap has to resolve to one readable panel rather
    # than both printed on top of each other. Fill-mode stays at none so these
    # values apply whenever the keyframes are not driving.
    return ('<div style="grid-area:1/1;opacity:%d;animation:%s 14s linear '
            'infinite">%s%s%s</div>' % (opacity, anim, head, body, foot))


def _lookup_json():
    ctx = ["prefers short replies, no preamble",
           "john works in insurance claims",
           "has a casual tone with john",
           "always asks for the source"]
    out = [_sp(PUNC, "{")]
    out.append('  ' + _sp(KEY, '"user"') + _sp(PUNC, ": ") +
               _sp(STR, '"u_8213"') + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"query"') + _sp(PUNC, ": ") +
               _sp(STR, '"Can you draft an email to john"') + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"context"') + _sp(PUNC, ": ["))
    for n, c in enumerate(ctx):
        out.append('    ' + _sp(STR, '"%s"' % c) +
                   (_sp(PUNC, ",") if n < len(ctx) - 1 else ""))
    out.append('  ' + _sp(PUNC, "]"))
    return "\n".join(out) + _sp(PUNC, "\n}")


def _answer_json():
    out = [_sp(PUNC, "{")]
    out.append('  ' + _sp(KEY, '"user"') + _sp(PUNC, ": ") +
               _sp(STR, '"u_8213"') + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"reply"') + _sp(PUNC, ": ") +
               _sp(STR, '"Hey John — file attached. Source: the Aug 14 export."') + _sp(PUNC, ","))
    out.append('  ' + _sp(KEY, '"context_applied"') + _sp(PUNC, ": ") +
               _sp(NUM, "4"))
    return "\n".join(out) + _sp(PUNC, "\n}")


def apply(out):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        i = s.find(START)
        if i == -1 or END not in s:
            continue
        j = s.index(END) + len(END)

        block = (
            '<div style="display:grid">'
            + _panel("api-a", 1, "GET", "/v1/&hellip;/users/{id}/context", "0.2s",
                     _lookup_json(),
                     "One call, before your prompt. No fine-tuning, no vector "
                     "store to run.")
            + _panel("api-b", 0, "POST", "/v1/&hellip;/chat/completions", "0.9s",
                     _answer_json(),
                     "The call your app already makes, answered with what it "
                     "knows. Under a second, end to end.")
            + '</div>'
        )
        s = s[:i] + block + s[j:]
        if "@keyframes api-a" not in s:
            s = s.replace("\n</style>", KEYFRAMES + "</style>", 1)
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  api demo rebuilt on %d pages" % n)
    if n == 0:
        print("  api demo card not found - still the old single panel - CHECK")
