/**
 * Contact form endpoint — submits to HubSpot.
 *
 * Runs as a Vercel serverless function beside the static site. The form POSTs
 * here; this re-validates (never trust the browser) and forwards to HubSpot's
 * Forms API, which creates or updates the contact in the CRM and fires
 * whatever notification and workflow you have configured on the form.
 *
 * Environment variables, set on the Vercel project:
 *
 *   HUBSPOT_PORTAL_ID   optional override; defaults to the live form
 *   HUBSPOT_FORM_GUID   optional override; defaults to the live form
 *   SITE_URL            canonical site address reported to HubSpot as the
 *                       submitting page. Must be a domain registered on the
 *                       HubSpot portal or submissions land in spam.
 *   HUBSPOT_USECASE_PROP  optional. Internal name of the property that holds
 *                         "what keeps forgetting". Defaults to "message",
 *                         which exists on every HubSpot account.
 *
 * Neither the portal id nor the form guid is a secret — this endpoint is the
 * public form-submission API and is safe to call from a browser. They live in
 * env vars anyway so the form can be repointed without a code change.
 *
 * Without them the endpoint returns 503 and the form tells the visitor to
 * email directly, rather than pretending the message was sent. A form that
 * silently discards leads is the bug this whole endpoint exists to replace.
 */

const REQUIRED = ["name", "email", "phone", "company", "country", "useCase"];
const MAX = 4000;

const clean = v => (typeof v === "string" ? v.trim().slice(0, MAX) : "");

function validate(body) {
  const out = {}, missing = [];
  for (const k of REQUIRED) {
    out[k] = clean(body[k]);
    if (!out[k]) missing.push(k);
  }
  out.message = clean(body.message);
  out.model = clean(body.model);
  if (out.email && !/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(out.email)) missing.push("email");
  return { out, missing: [...new Set(missing)] };
}

/**
 * HubSpot stores people as firstname + lastname; the form asks for one name,
 * because two boxes for a name is friction nobody thanks you for. Split on the
 * first space and put everything else in the surname — wrong for some naming
 * conventions, but it keeps the full string intact and searchable either way.
 */
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

  // Bots fill every field they can find, including one hidden off-screen.
  if (clean(body.website)) return res.status(200).json({ ok: true });

  const { out, missing } = validate(body);
  if (missing.length) return res.status(422).json({ error: "Missing fields", missing });

  // Defaults are the live SapientPriors form. Neither value is a secret —
  // this is the public submission endpoint a browser is meant to call — so
  // they are committed rather than hidden, and the env vars stay available
  // to repoint the form without a deploy.
  const portal = process.env.HUBSPOT_PORTAL_ID || "246939253";
  const guid = process.env.HUBSPOT_FORM_GUID || "23455ad3-6bc4-4c4b-a316-418d6a598326";
  if (!portal || !guid) {
    return res.status(503).json({
      error: "Form is not connected yet",
      hint: "Set HUBSPOT_PORTAL_ID and HUBSPOT_FORM_GUID in the Vercel project."
    });
  }

  const useCaseProp = process.env.HUBSPOT_USECASE_PROP || "message";
  const { firstname, lastname } = splitName(out.name);

  const fields = [
    { name: "firstname", value: firstname },
    { name: "lastname", value: lastname },
    { name: "email", value: out.email },
    { name: "phone", value: out.phone },
    { name: "company", value: out.company },
    { name: "country", value: out.country },
    { name: "model_in_use", value: out.model },
    {
      name: useCaseProp,
      value: out.message ? `${out.useCase}\n\n---\n${out.message}` : out.useCase
    }
  ].filter(f => f.value);

  /*
    pageUri is deliberately NOT taken from the Referer header.

    HubSpot checks the submitting domain against the site domains registered on
    the portal and silently routes anything else to Spam Submissions with type
    "Unregistered Site Domain" — the submission is stored, no contact is
    created, and the endpoint still gets a 200, so nothing surfaces as an
    error. Forwarding the referer meant every real browser submission from
    sapientpriors-site.vercel.app was quietly binned while curl tests, which
    send no referer and so fell back to the canonical domain, sailed through.

    Sending the canonical site URL keeps this stable across preview
    deployments, branch URLs and the eventual custom domain. Override with
    SITE_URL if the canonical address changes.
  */
  const siteUrl = process.env.SITE_URL || "https://sapientpriors.com/";

  const payload = {
    fields,
    context: {
      pageUri: siteUrl,
      pageName: "Contact — book a working session"
    }
  };

  // Passed through when the HubSpot tracking script is present, so the
  // submission is attributed to that visitor's session rather than landing
  // as an anonymous contact. Harmless when absent.
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
      console.error("hubspot rejected", r.status, detail);
      // 400 from HubSpot almost always means a field name that does not exist
      // as a property on the form — surface it in the logs, not to the visitor.
      return res.status(502).json({ error: "The CRM rejected the submission" });
    }
    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error("contact endpoint threw", err);
    return res.status(500).json({ error: "Could not send" });
  }
}
