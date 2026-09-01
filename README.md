# SapientPriors

The marketing site. Static HTML with two serverless functions — no framework,
no build step at deploy time.

## Layout

```
index.html            the home page (a copy of SapientPriors.dc.html)
*.dc.html             one file per page: Team, Careers, TryIt, Pricing, …
SiteNav / SiteFooter  shared components, imported by every page
support.js            the Claude Design runtime that renders the pages
try-demo.js           the Try It demo
apply-form.js         the careers application form
api/contact.js        contact form  -> HubSpot
api/apply.js          job application -> HubSpot
art/ fonts/ logos/    assets
build/                the pipeline that turns a raw export into this
```

## Deploying

There is no build. Vercel serves the repo root as static files and picks up
`api/*.js` as functions. `vercel.json` sets cache headers and the noindex
header; it deliberately sets no `buildCommand` or `outputDirectory`.

**A Vercel project that previously built this repo needs its settings cleared**
— Framework Preset "Other", Build Command empty, Output Directory empty.
Vercel falls back to the dashboard values for anything `vercel.json` does not
specify, so a leftover `npm run build` will fail against a repo that has no
`package.json`.

No environment variables are required. The API routes carry working defaults
and accept overrides:

| Variable | Default |
|---|---|
| `HUBSPOT_PORTAL_ID` | `246939253` |
| `HUBSPOT_FORM_GUID` | the "Website — book a working session" form |
| `HUBSPOT_APPLY_FORM_GUID` | the "Careers — role application" form |
| `SITE_URL` | `https://sapientpriors.com/` |

Neither the portal id nor a form guid is a secret — this is the public form
submission API, designed to be called from a browser.

`SITE_URL` is reported to HubSpot as the submitting page and **must be a domain
registered on the HubSpot portal**, or submissions are silently filed as spam
with no contact created and a 200 returned. It is deliberately not taken from
the `Referer` header for that reason.

## Rebuilding from a Claude Design export

```
python3 build/build.py ~/Downloads/SapientPriors-website2
```

Converts images to WebP, re-encodes the hero video from HEVC to H.264,
repoints assets, then re-applies every change in `build/patch_*.py` on top of
the raw export. Anything fixed here must go in a patch module, or the next
export silently reverts it.
