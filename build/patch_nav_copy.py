# -*- coding: utf-8 -*-
"""
Nav shape, the CTA label, and the careers hero copy.

Nav: Team and Careers come out of the Company menu to sit alongside Docs, so the
two pages a visitor is most likely to want are one click rather than two. Order
is Docs, Team, Company, Careers. Company keeps About and Contact.

CTA: "Get access" becomes "Get beta access", which says what is actually on
offer.

Careers: the hero subtext stated a count and a single location, and both were
wrong - it said two roles in Bangalore while the page listed four and the
form accepted four, one of them remote-friendly. A page that contradicts its own
listings on the same screen is worse than one that says less, so the count comes
out entirely rather than being corrected to a number that will go stale again
the next time a role opens.

The line "Small team, so whatever you ship goes to production with your name on
it" is gone. It promised credit rather than work, which reads as a pitch dressed
as a fact.
"""
import glob
import io
import os

OLD_GROUPS = """const GROUPS = [
  { label: 'Docs', href: 'API%20Docs.dc.html' },
  { label: 'Company', items: [
    { label: 'About', href: HOME + '#lab', description: 'The lab and how we work' },
    { label: 'Team', href: 'Team.dc.html', description: 'Who is building it' },
    { label: 'Careers', href: 'Careers.dc.html', description: 'Two open roles in Bangalore' },
    { label: 'Contact', href: HOME + '#access', description: 'Book a working session' }
  ] }
];"""

NEW_GROUPS = """const GROUPS = [
  { label: 'Docs', href: 'API%20Docs.dc.html' },
  { label: 'Team', href: 'Team.dc.html' },
  { label: 'Company', items: [
    { label: 'About', href: HOME + '#lab', description: 'The lab and how we work' },
    { label: 'Contact', href: HOME + '#access', description: 'Book a working session' }
  ] },
  { label: 'Careers', href: 'Careers.dc.html' }
];"""

OLD_SUB = ("Two roles, both in Bangalore, both hybrid. Small team, so whatever "
           "you ship goes to production with your name on it. Mentorship from "
           "ML veterans with twelve years behind them.")
NEW_SUB = ("Remote and Bangalore, hybrid. You will work close to the research, "
           "with mentorship from ML veterans with twelve years behind them.")

# Every call to action on the site says the same thing, in title case: the nav
# button, the hero button, and the ones in the page body. "Get API access" named
# the artefact; "Get Beta Access" names the thing being offered, and two labels
# for one action read as two different actions.
CTA_TO = ">Get Beta Access<"
CTA_FROM = (">Get access<", ">Get beta access<", ">Get API access<")


def apply(out):
    nav = sub = cta = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        before = s
        if OLD_GROUPS in s:
            s = s.replace(OLD_GROUPS, NEW_GROUPS, 1)
            nav += 1
        if OLD_SUB in s:
            s = s.replace(OLD_SUB, NEW_SUB, 1)
            sub += 1
        for label in CTA_FROM:
            if label in s:
                cta += s.count(label)
                s = s.replace(label, CTA_TO)
        if s != before:
            io.open(path, "w", encoding="utf-8",
                    errors="surrogateescape").write(s)
    print("  nav regrouped on %d, careers subtext on %d, CTA relabelled %d times"
          % (nav, sub, cta))
    if nav == 0:
        print("  nav GROUPS not found - menu unchanged - CHECK")
    if sub == 0:
        print("  careers subtext not found - CHECK")
    if cta == 0:
        print("  CTA label not found - CHECK")
