/**
 * Careers application endpoint — submits to HubSpot.
 *
 * Deliberately a separate form from the contact one, with its own GUID and its
 * own notification. Folding applicants into "Website — book a working session"
 * would have made the two indistinguishable in the CRM and in the inbox, so
 * neither could be filtered or reported on. Same reason this is a separate
 * route rather than a flag on /api/contact: one endpoint, one form, one
 * meaning.
 *
 * Environment variables, set on the Vercel project:
 *
 *   HUBSPOT_PORTAL_ID        optional override; defaults to the live portal
 *   HUBSPOT_APPLY_FORM_GUID  optional override; defaults to the live form
 *   SITE_URL                 canonical site address reported to HubSpot. Must
 *                            be a domain registered on the portal or the
 *                            submission is silently routed to spam.
 *
 * Neither the portal id nor the form guid is a secret — this is the public
 * form-submission API, meant to be called from a browser.
 */

/*
  q1-q3 are required because every question set has at least three; q4 only
  exists for the research roles, so it is optional here and enforced in the
  form, which knows which set was shown.
*/
const REQUIRED = ["name", "email", "phone", "country", "role", "school",
                  "resumeLink", "q1", "q2", "q3"];
const MAX = 4000;

/*
  The dropdown sends the label; HubSpot stores the internal value. Mapping here
  rather than putting values in the markup keeps the page readable and means a
  renamed role is a one-line change in one place. Anything not on this list is
  rejected rather than passed through, so the property cannot accumulate
  free-text variants of its own options.
*/
const ROLES = {
  "Machine Learning Engineer": "ml_engineer",
  "Machine Learning Engineer Intern": "ml_engineer_intern",
  "Founders Office": "founders_office",
  "Software Engineer, Distributed Systems": "software_engineer"
};

const clean = v => (typeof v === "string" ? v.trim().slice(0, MAX) : "");

function validate(body) {
  const out = {}, missing = [];
  for (const k of REQUIRED) {
    out[k] = clean(body[k]);
    if (!out[k]) missing.push(k);
  }
  out.message = clean(body.message);
  out.q4 = clean(body.q4);

  if (out.email && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(out.email)) missing.push("email");
  if (out.role && !ROLES[out.role]) missing.push("role");

  // A resume "link" that is not a link is the single most common way this form
  // fails usefully-looking: the row arrives complete and the one field the
  // whole application turns on cannot be opened.
  if (out.resumeLink && !/^https?:\/\/[^\s]+\.[^\s]+/i.test(out.resumeLink)) {
    missing.push("resumeLink");
  }
  return { out, missing: [...new Set(missing)] };
}

function splitName(full) {
  const parts = full.split(/\s+/);
  return parts.length === 1
    ? { firstname: parts[0], lastname: "" }
    : { firstname: parts[0], lastname: parts.slice(1).join(" ") };
}

export default async function handler(req, res) {
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Method not allowed" });
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { return res.status(400).json({ error: "Bad JSON" }); }
  }
  body = body || {};

  if (clean(body.website)) return res.status(200).json({ ok: true });

  const { out, missing } = validate(body);
  if (missing.length) return res.status(422).json({ error: "Missing fields", missing });

  const portal = process.env.HUBSPOT_PORTAL_ID || "246939253";
  const guid = process.env.HUBSPOT_APPLY_FORM_GUID || "cf0b4874-f528-4b7b-b447-f491474c787c";
  if (!portal || !guid) {
    return res.status(503).json({
      error: "Applications are not connected yet",
      hint: "Set HUBSPOT_PORTAL_ID and HUBSPOT_APPLY_FORM_GUID in the Vercel project."
    });
  }

  const { firstname, lastname } = splitName(out.name);
  const fields = [
    { name: "firstname", value: firstname },
    { name: "lastname", value: lastname },
    { name: "email", value: out.email },
    { name: "phone", value: out.phone },
    { name: "country", value: out.country },
    { name: "role_applied_for", value: ROLES[out.role] },
    { name: "school", value: out.school },
    { name: "resume_link", value: out.resumeLink },
    { name: "app_q1", value: out.q1 },
    { name: "app_q2", value: out.q2 },
    { name: "app_q3", value: out.q3 },
    { name: "app_q4", value: out.q4 },
    { name: "message", value: out.message }
  ].filter(f => f.value);

  // Not the Referer header — see the note in contact.js. HubSpot silently
  // routes submissions from unregistered domains to spam, which looks like
  // success from here.
  const siteUrl = process.env.SITE_URL || "https://sapientpriors.com/";

  const payload = {
    fields,
    context: { pageUri: siteUrl, pageName: "Careers — role application" }
  };
  const hutk = (req.headers.cookie || "").match(/hubspotutk=([^;]+)/);
  if (hutk) payload.context.hutk = hutk[1];

  try {
    const r = await fetch(
      `https://api.hsforms.com/submissions/v3/integration/submit/${portal}/${guid}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      }
    );
    if (!r.ok) {
      const detail = await r.text();
      console.error("hubspot rejected application", r.status, detail);
      return res.status(502).json({ error: "The CRM rejected the application" });
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error("apply endpoint threw", err);
    return res.status(500).json({ error: "Could not send" });
  }
}
