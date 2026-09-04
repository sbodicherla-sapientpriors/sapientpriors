# SapientPriors website — working on it

Written for someone (or someone's agent) picking this up to change copy and
content without breaking it. Read "Where the copy lives" and "Changing copy
safely" first; the rest is reference.

---

## 1. Where everything is

| | |
|---|---|
| **Company repo** | `github.com/SapientPriors-Inc/sapientpriors` — the canonical home, work here |
| **Deploy repo** | `github.com/sbodicherla-sapientpriors/sapientpriors` — a fork; **this is the one Vercel currently builds** |
| **Live site** | https://www.sapientpriors.com |
| **Host** | Vercel, static, with two serverless functions under `api/` |
| **Internal review repo** | `github.com/sbodicherla-sapientpriors/sapientpriors-site` — same site, permanently de-indexed |

Everything served is committed. There is no build step on Vercel: what is in the
repo root is what is served.

### Read this before pushing

There are two repos and they are not interchangeable **yet**.

The Vercel project that serves sapientpriors.com is connected to the *fork*, not
to the company repo. So today:

- push to the **company repo** — that is where the work belongs and where PRs
  should be opened;
- also push to the **fork**, or the change does not go live.

Both are currently identical, and a change must reach both until the Vercel
project is re-pointed at the company repo. Once that is done, the fork can be
retired and this becomes one repo. Whoever owns the Vercel project needs to make
that change; see the end of this file.

---

## 2. How the site is actually built

The design is authored in **Claude Design** and exported as `.dc.html` files.
The export is not deployable as-is, so a Python pipeline rewrites it:

```
Claude Design export  ──►  build/build.py  ──►  the .html files in this repo
```

```bash
python3 build/build.py <path to the design export>
```

**The export is not in this repo.** Only its output is. So you can run the site
locally and edit the built files, but you cannot re-run the build without the
export folder. Ask Harsha for it if you need to.

**This is the single most important thing to understand:** every `.dc.html` file
and `index.html` in this repo is *generated*. Re-exporting the design overwrites
all of them. Wording typed straight into a built page works until the next
export and then silently reverts. That is why `build/patch_copy.py` exists.

### The patch modules

`build/build.py` runs these in order. Each one fixes something the export gets
wrong or cannot express:

| module | what it owns |
|---|---|
| `patch_contact.py` | the home contact form: fields, validation, success state |
| `patch_content.py` | factual corrections re-applied after each export |
| `patch_ui.py` | the big one (~2000 lines): hero, charts, stat tiles, use-case cards, careers roles and JD, team, footer, alumni strip |
| `patch_nav_copy.py` | nav shape, the CTA label, careers hero subtext |
| `patch_address.py` | the footer address |
| `patch_copyright.py` | the copyright line (year from the build clock) |
| `patch_api_demo.py` | the rotating API card in the hero |
| **`patch_copy.py`** | **plain wording overrides — start here** |
| `patch_urls.py` | clean URLs, `rel=canonical`, `sitemap.xml` |
| `patch_head.py` | `<title>`, favicon, `overflow-x:clip`, analytics + intent scripts |
| `patch_motion.py` | injects `scroll-motion.js` |
| `patch_seo.py` | **review build only** — the noindex layers |

Every module prints a `CHECK` line if a string it was looking for is missing.
**A build with `CHECK` in the output is a failed build**, even though it exits 0.
The failure mode this whole pipeline is designed around is the silent no-op:
a replacement that matches nothing and changes nothing.

---

## 3. Changing copy safely

Add a `(find, replace)` pair to `COPY` in **`build/patch_copy.py`**:

```python
COPY = [
    ("Agents that learn from every conversation",
     "Agents that remember every conversation"),
]
```

Rebuild, and check the output:

```bash
python3 build/build.py <path to the design export>
```

It prints `copy: N of M overrides applied`, and names any pair that matched
nothing with a `CHECK`. Do not ignore that — it means your wording is not live.

Two things that bite:

- **Copy the find-text out of the page, do not retype it.** The site uses
  typographic quotes and dashes (`'` `'` `"` `"` `—` `–`) that look identical to
  the ASCII ones and do not compare equal. This has cost real time here already.
- Pairs apply to **every** generated page, including `SiteNav.dc.html` and
  `SiteFooter.dc.html`, so a header or footer string needs only one pair.

**If you cannot run the build** (no export folder), edit the built `.html` files
directly, open the PR, and say so in the description — someone will mirror the
change into `patch_copy.py` so it survives the next export.

---

## 4. Where the copy lives

Most prose is in the export and can be changed with a `patch_copy.py` pair. The
exceptions are things built by JavaScript at runtime — for those, edit the named
module.

| what | where |
|---|---|
| Hero headline and sub-line | `patch_ui.py` (search `Agents that learn`) |
| Hero API card — paths, query, context, output, captions | `patch_api_demo.py`, the `EXAMPLES` list at the top |
| Stat tiles (200% / 95 / 91.6) | `patch_ui.py`, `const TILES` |
| Chart data and the two callouts | `patch_ui.py`, `ACCURACY` / `COST` / `annotation(...)` |
| "How it works" steps 01–03 | export — `patch_copy.py` pair |
| Use-case cards | `patch_ui.py`, `UC_LOGOS` and the card list |
| Alumni strip (logos, captions, sizing) | `patch_content.py` |
| Team members | `patch_ui.py`, the `LEADERS`-style list |
| Careers roles, JDs, locations | `patch_ui.py`, `_careers_roles` |
| Careers application questions | `apply-form.js`, `QUESTIONS` and `HINTS` |
| Careers hero subtext | `patch_nav_copy.py` |
| Nav items and CTA label | `patch_nav_copy.py`, `NEW_GROUPS` and `CTA_TO` |
| Footer address / copyright | `patch_address.py` / `patch_copyright.py` |
| Contact form fields and copy | `patch_contact.py` |
| Page `<title>`s | `patch_head.py`, `TITLES` |

**Known open copy work:** use-case cards 3–6 still carry template text
("Customer Support Chatbots", "Content Writers", "Shopping Assistants",
"Virtual Assistants"). The legal pages (Privacy, Terms, Cookie, Security) are
`mailto:` placeholders. `/research` and `/pricing` say they are still being
built and carry a `noindex` because of it.

---

## 5. Running it locally

```bash
cd <repo>
python3 -m http.server 5173
open http://localhost:5173/index.html
```

Static server only — no build, no npm. Two caveats:

- Locally you must use the file names (`/Careers.dc.html`), not the clean paths
  (`/careers`). Clean URLs are Vercel rewrites and only exist when deployed.
- `api/contact` and `api/apply` do not run locally, so form submission fails.
  Everything else works.

The page holds a ~3s intro curtain. Give it 4 seconds before judging anything.

---

## 6. Getting a private draft site

Two options. Both keep production untouched.

### Option A — a Vercel preview (fastest)

Push any branch that is not `main`:

```bash
git checkout -b copy-pass
# ...edit...
git commit -am "copy: first pass"
git push -u origin copy-pass
```

Vercel builds it and comments a preview URL on the PR (`*.vercel.app`). It is a
full working copy of the site at that branch.

**Add the noindex yourself — do not assume the preview is private.** The
simplest belt-and-braces version, in the branch only:

1. In `vercel.json`, add to `headers`:
   ```json
   { "source": "/(.*)", "headers": [
       { "key": "X-Robots-Tag", "value": "noindex, nofollow" } ] }
   ```
2. Replace `robots.txt` with:
   ```
   User-agent: *
   Disallow: /
   ```
3. Delete `sitemap.xml` from the branch.

Drop all three from the branch before merging, or production goes invisible.
That mistake is easy to make and slow to notice.

### Option B — the review repo (already set up)

`github.com/sbodicherla-sapientpriors/sapientpriors-site` is the same site with
`patch_seo.py` in the pipeline, which applies three layers of de-indexing:
`robots.txt` disallow, a `noindex` meta on every page, and an `X-Robots-Tag`
header covering files a crawler reaches without parsing HTML. It is permanently
safe to share by link. There is no password — link-only, not gated.

---

## 7. Shipping a change

```bash
git checkout -b <branch>
# edit; rebuild if you have the export
git commit -am "..."
git push -u origin <branch>
gh pr create --base main
```

Merging to `main` on the **fork** deploys to production within about a minute.
Merging on the company repo does not deploy anything yet — see "Read this before
pushing" above. Then verify
against the live site, not the local one:

```bash
curl -sL https://www.sapientpriors.com/ | grep -c "your new wording"
```

**Before opening the PR:**

- [ ] build output has no `CHECK` lines
- [ ] every copy override reported as applied
- [ ] loaded `/`, `/careers`, `/docs` with no console errors
- [ ] no horizontal scrollbar at 1440px and at 390px
- [ ] nav and footer still render (they are fetched at runtime — see §9)
- [ ] no noindex left over from a draft branch

---

## 8. What the site is made of

No framework, no bundler, no npm. Plain HTML, CSS and vanilla JS.

| file | what it does |
|---|---|
| `support.js` | the Claude Design runtime (vendored — do not edit) |
| `scroll-motion.js` | line reveals, staggered rises, smooth scroll, in-page anchors |
| `chart-scroll.js` | draws the two benchmark charts progressively on scroll |
| `apply-form.js` | the careers application form, including per-role questions |
| `try-demo.js` | the Try It page |
| `image-slot.js` | image handling |
| `api/contact.js` | home form → HubSpot |
| `api/apply.js` | careers form → a *different* HubSpot form, on purpose |

### Motion

Modelled on a reference site, rebuilt from scratch. No animation library.

- **Line reveal** — headings are split into lines, each clipped by its own
  parent and starting below it, so it wipes up. 1.2s,
  `cubic-bezier(.165,.84,.44,1)`, 0.08s apart.
- **Rise + stagger** — sub-heads and card rows fade up 22px, children 0.09s apart.
- **Smooth scroll** — the page eases to where the wheel put it. Implemented
  against `window.scrollTo`, not by transforming a wrapper, because a
  transformed wrapper breaks the fixed nav and sticky sections.
- **Parallax** — written, correct, and **off**: the site has one photograph, and
  one drifting image among logos reads as a fault. `?motion=lines,stagger,smooth,parallax`
  turns it on.
- Reveals **replay** when you scroll back up, deliberately. There is no
  `prefers-reduced-motion` gate, also deliberately.
- The rotating API card is pure CSS — two panels in one grid cell, two keyframe
  tracks 50% out of phase. No script to re-arm when the runtime re-renders.

---

## 9. Gotchas that have already cost time

Read this section before debugging anything.

1. **The runtime replaces DOM nodes after hydration.** A script that mounts once
   on load will be silently wiped. Anything that touches the DOM needs a
   `MutationObserver` attached unconditionally, not just on first-mount failure.

2. **`SiteNav.dc.html` and `SiteFooter.dc.html` are fetched at runtime by every
   page.** They look like stray fragments with no inbound links, and the obvious
   move is to redirect or delete them. Doing that removes the nav and footer
   from the entire site.

3. **The runtime strips `required` from inputs.** Native form validation never
   runs. All validation lives in the submit handlers.

4. **The runtime rewrites nodes carrying `sc-interp` or `data-count` bindings.**
   Those cannot be restructured — that is why some headings get a rise instead
   of a line-wipe.

5. **The runtime drops the last whitespace text node in a `<pre>`.** A closing
   brace on its own line lands welded to the value above it. Put the newline
   inside the span.

6. **A grid item defaults to `min-width:auto`**, so a long `<pre>` line pushes
   the panel wider than the card holding it. `min-width:0`.

7. **Section entrance animations translate horizontally**, so the document is
   wider than the window mid-flight. `html,body{overflow-x:clip}` handles it —
   `clip`, not `hidden`, because `hidden` makes the element a scroll container
   and breaks `position:sticky`.

8. **Vercel routes on the percent-encoded path.** A rule for
   `/Company Brain.dc.html` matches nothing; it needs `%20`. And a rule that
   matches nothing fails silently — check against the live response, not the
   config.

9. **Nav hrefs are generated by the runtime from page names.** They cannot
   always be rewritten at build time. `scroll-motion.js` intercepts clicks whose
   fragment names an element on the current page and scrolls in-page instead.

10. **CSS animations override inline transforms.** This broke the curtain
    wordmark's centring once.

11. `zsh` mangles non-ASCII in shell variables. Write to a file and grep it.

---

## 10. URLs, SEO and measurement

- Clean paths — `/docs`, `/careers`, `/team`, `/try`, `/research`, `/pricing` —
  are **rewrites** in `vercel.json`. The old `.dc.html` paths **308** to them.
- Every page carries `rel=canonical` pointing at its clean URL.
- `sitemap.xml` lists only the indexable set; `/research` and `/pricing` are
  excluded because they carry a `noindex` while unfinished.
- `build/` is excluded from the deployment by `.vercelignore` — it was being
  served as readable source.
- Two scripts in `<head>`: a buying-intent tracker and Cloudflare Web Analytics
  (cookieless, so no consent banner). Both are excluded from the nav and footer
  fragments — a script there fires three times per page view.

---

## 11. Forms

Both post to HubSpot, to **two different forms on purpose**, so applications and
sales leads can be filtered apart.

- `api/contact.js` — home page. Required: name, email, company.
- `api/apply.js` — careers. Required: the base fields, resume link, and the
  first three role questions.

`apply-form.js` holds `QUESTIONS` and `HINTS`, keyed by role label. **The keys
must match the dropdown labels exactly** — a typographic apostrophe in one and
an ASCII one in the other renders identically and silently falls through to the
default question set. That has happened.

The role labels must also match the `role_applied_for` enumeration in HubSpot,
or submissions for that role are rejected.

No secrets are in this repo. The HubSpot portal ID and form GUIDs are public by
design; the private token lives only in Vercel's environment variables.


---

## 12. Outstanding: one repo instead of two

The Vercel project serving sapientpriors.com is connected to
`sbodicherla-sapientpriors/sapientpriors`, a fork, rather than to the company
repo. That is why every change has to be pushed twice.

To fix it, on the Vercel project that owns the `sapientpriors.com` domain:

1. **Settings → Git → Disconnect**
2. **Connect Git Repository →** `SapientPriors-Inc/sapientpriors`, branch `main`
3. Redeploy, and check the live site still serves 200 and still carries
   `rel=canonical` and the analytics beacon
4. Then the fork can be archived, and this section deleted

Until then, pushing only to the company repo will look like it worked and change
nothing on the live site.
