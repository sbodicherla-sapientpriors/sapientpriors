/**
 * /api/try — the endpoint behind the Try It playground.
 *
 * Up to three contenders answer one question about the MG Hector owner's manual, and
 * the page times them. This function is the only authenticated party: the browser holds
 * no credential for anything, and every visitor is anonymous.
 *
 * The page currently asks for "ours" only — the two rival panes are switched off there,
 * not here. They are kept implemented because switching them back on is a two-line
 * change in try-demo.js, and because the asymmetry below is the argument the page makes
 * when they are on.
 *
 * ── Why the three panes are not symmetrical ─────────────────────────────────
 * "ours" asks the product API, which retrieves from memory and streams an answer
 * whose first token arrives without the document in context at all.
 *
 * "opus" is handed the whole 288-page PDF on every question, cached so a burst of
 * visitors shares one cache write. It works, and it is slow and expensive — which is
 * the comparison the page exists to make.
 *
 * "haiku" is handed the same PDF and the API refuses it: document blocks cap at 600
 * pages on 1M-context models but 100 on 200K-context ones, and Haiku 4.5 is 200K. The
 * pane reports the refusal. We do not simulate this and must never start: the whole
 * claim is that the limit is real, so the day Anthropic raises that cap the honest
 * thing is for this pane to start working.
 *
 * ── Identity ────────────────────────────────────────────────────────────────
 * The thread id lives in an HttpOnly cookie, never in page JS. Two reasons: page JS
 * cannot leak it into a screenshot or a paste, and the visitor cannot hand someone
 * else a link into their own conversation. The typed username is a display name only
 * — keying threads on it would mean two visitors who both chose "Ravi" land in one
 * thread and read each other's conversation, which is impersonation on a page with no
 * login. IP is used for rate limiting and never for identity: office NATs collapse
 * many visitors into one and phones change IP mid-session.
 *
 * ── Why the PDF is a file_id and not bytes ──────────────────────────────────
 * The manual is 10.2MB. Inlining it base64 costs ~13.6MB uploaded per question per
 * rival pane, which is the request body, not the token bill — prompt caching does not
 * help with it. The Files API stores it once (see deploy/upload-manual.mjs) and every
 * request references the id. cache_control on the document block is what makes the
 * token side cheap on top of that.
 *
 * ── Environment ─────────────────────────────────────────────────────────────
 *   PRODUCT_API_BASE_URL      the demo API's origin; also the ID token audience
 *   PLAYGROUND_AGENT_ID       the agent that owns the manual
 *   ANTHROPIC_API_KEY         for the two rival panes
 *   ANTHROPIC_MANUAL_FILE_ID  the manual, uploaded once to the Files API
 * Google credentials come from Vercel's OIDC exchanged through Workload Identity
 * Federation (GCP_WORKLOAD_IDENTITY_PROVIDER + GCP_SERVICE_ACCOUNT_EMAIL), so no
 * long-lived key is stored; GOOGLE_SERVICE_ACCOUNT_KEY is the fallback for a project
 * where federation is not set up. Without them the endpoint answers 503 and the pane
 * says it is not connected, rather than inventing a reply — a demo whose whole claim
 * is "it answers from this document" cannot afford a scripted answer that only looks
 * like one.
 */

import Anthropic from "@anthropic-ai/sdk";
import { ExternalAccountClient, GoogleAuth, Impersonated } from "google-auth-library";

// Fluid compute: a rival pane reading 288 pages runs well past the 10s default, and a
// truncated stream is indistinguishable to the page from a slow one.
export const config = { maxDuration: 300 };

const MODELS = {
  opus: "claude-opus-5",
  haiku: "claude-haiku-4-5",
};

const API_BASE = (process.env.PRODUCT_API_BASE_URL || "").replace(/\/+$/, "");
const AGENT_ID = process.env.PLAYGROUND_AGENT_ID || "";
const MANUAL_FILE_ID = process.env.ANTHROPIC_MANUAL_FILE_ID || "";
const COOKIE = "sp_try_thread";
const THREAD_TTL_SECONDS = 60 * 60 * 24 * 30;

const SYSTEM = [
  "You answer questions about the MG Hector owner's manual, which is attached.",
  "Answer only from the manual. If it does not cover something, say so.",
  "Be brief: two or three sentences unless the reader asks for steps.",
].join(" ");

/** Answers stream as SSE so the page can time the first token. One frame shape for
 *  all three panes, so the client has one reader rather than three. */
function sse(res, event, data) {
  res.write(`event: ${event}\ndata: ${JSON.stringify(data)}\n\n`);
}

/* ── rate limiting ─────────────────────────────────────────────────────────
   In-process and per-instance: a burst that lands on four Vercel instances gets four
   windows, and a cold start forgets everything. That ceiling is deliberate — it costs
   nothing, needs no store, and still stops the one case that actually bites, which is
   a single client looping the endpoint. Upgrade path when the page gets traffic worth
   metering: Vercel KV or Upstash, same window, same key.
*/
const WINDOW_MS = 60_000;
const MAX_PER_WINDOW = 12;
const hits = new Map();

function overLimit(ip) {
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  // Unbounded growth is the failure mode of a Map keyed on client input; one sweep per
  // call over a map that only holds a minute of traffic is cheaper than a timer.
  if (hits.size > 5000) {
    for (const [key, times] of hits) {
      if (!times.length || now - times[times.length - 1] > WINDOW_MS) hits.delete(key);
    }
  }
  return recent.length > MAX_PER_WINDOW;
}

function clientIp(req) {
  const forwarded = req.headers["x-forwarded-for"];
  return String(forwarded || "").split(",")[0].trim() || req.socket?.remoteAddress || "unknown";
}

/* ── the product API ───────────────────────────────────────────────────────── */

let tokenClient = null;

/** A Google ID token for the product API, minted as the playground service account.
 *  The client is cached across invocations on a warm instance; google-auth-library
 *  refreshes the token itself, so caching the client is what avoids a token exchange
 *  per question without ever serving an expired one. */
async function productToken() {
  if (!API_BASE) return null;
  if (!tokenClient) {
    const provider = process.env.GCP_WORKLOAD_IDENTITY_PROVIDER;
    const account = process.env.GCP_SERVICE_ACCOUNT_EMAIL;
    // WHY this branch is first and guarded on the ABSENCE of provider: it is the local
    // path, and it must be impossible for it to win on Vercel, which always sets one.
    if (!provider && account && !process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
      /*
        WHY a third path: with no federation and no key, there is no way to run this
        endpoint on a laptop, and an endpoint nobody can run locally gets debugged in
        production. Application Default Credentials impersonating the same service
        account gives a developer the same token the deployment gets, from
          gcloud auth application-default login \
            --impersonate-service-account=<GCP_SERVICE_ACCOUNT_EMAIL>
        It is never the path in production: Vercel sets GCP_WORKLOAD_IDENTITY_PROVIDER.
      */
      tokenClient = new Impersonated({
        sourceClient: await new GoogleAuth().getClient(),
        targetPrincipal: account,
        lifetime: 3600,
        delegates: [],
        targetScopes: ["https://www.googleapis.com/auth/cloud-platform"],
      });
    } else if (provider && account && process.env.VERCEL_OIDC_TOKEN) {
      /*
        Two steps, not one. The federated client can only exchange Vercel's OIDC token
        for an access token; it has no fetchIdToken, and the product API wants an ID
        token with a specific audience. Impersonated wraps it and calls the IAM
        Credentials generateIdToken endpoint, which is the piece that produces one.

        The supplier reads the env var per call rather than closing over it: Vercel
        rotates VERCEL_OIDC_TOKEN, and a warm instance that captured the value at
        construction would keep presenting an expired assertion until it died.
      */
      const federated = ExternalAccountClient.fromJSON({
        type: "external_account",
        audience: provider,
        subject_token_type: "urn:ietf:params:oauth:token-type:jwt",
        token_url: "https://sts.googleapis.com/v1/token",
        subject_token_supplier: {
          getSubjectToken: async () => process.env.VERCEL_OIDC_TOKEN,
        },
      });
      tokenClient = new Impersonated({
        sourceClient: federated,
        targetPrincipal: account,
        lifetime: 3600,
        delegates: [],
        targetScopes: ["https://www.googleapis.com/auth/cloud-platform"],
      });
    } else if (process.env.GOOGLE_SERVICE_ACCOUNT_KEY) {
      // The fallback for a project without federation set up. A JWT client signs its
      // own ID token from the key, so there is nothing to impersonate.
      const auth = new GoogleAuth({
        credentials: JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_KEY),
      });
      tokenClient = await auth.getClient();
    } else {
      return null;
    }
  }
  // The audience IS the Cloud Run URL: the server checks it, so a token minted for
  // anything else is rejected there rather than accepted with the wrong scope here.
  return tokenClient.fetchIdToken(API_BASE);
}

function readCookie(req, name) {
  const raw = req.headers.cookie || "";
  for (const part of raw.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key === name) return decodeURIComponent(rest.join("="));
  }
  return null;
}

/** The visitor's thread, created on first question and remembered in an HttpOnly
 *  cookie. Path is scoped to this endpoint so it is not attached to page or asset
 *  requests, where it would be nothing but a tracking identifier. */
async function ensureThread(req, res, token, username) {
  const existing = readCookie(req, COOKIE);
  if (existing) return existing;
  const made = await fetch(`${API_BASE}/api/v1/agents/${encodeURIComponent(AGENT_ID)}/threads`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ title: `Playground — ${username || "anonymous"}`, metadata: {} }),
  });
  if (!made.ok) throw new Error(`thread create failed: ${made.status}`);
  const thread = (await made.json()).thread_id;
  res.setHeader(
    "Set-Cookie",
    `${COOKIE}=${encodeURIComponent(thread)}; HttpOnly; Secure; SameSite=Lax; ` +
      `Path=/api/try; Max-Age=${THREAD_TTL_SECONDS}`,
  );
  return thread;
}

/* ── citations ─────────────────────────────────────────────────────────────
   Every answer also cites the parent PDF, which on this page says nothing: there is
   exactly one document and it is already open in the left pane. Only the figure crops
   are shown, because a diagram of the thing you asked about is evidence a visitor can
   check, and it is the half of the claim the prose cannot carry.

   The label is rebuilt too. The product returns the stored crop's filename, which is
   the upload's name plus an ordinal ("manual4.pdf_img-19.jpg") — an internal artefact
   that would put our own re-upload bookkeeping on a public page.
*/
function isFigure(c) {
  return String(c.media_type || "").startsWith("image/");
}

function asFigure(c) {
  const ordinal = /img-(\d+)/.exec(c.label || "");
  return {
    label: ordinal ? `Figure ${ordinal[1]}` : "Figure",
    media_type: c.media_type,
    // The product's href points at an authenticated route the browser cannot call,
    // so it is rewritten to this function's own proxy.
    href: `/api/try?source=${encodeURIComponent(c.source_id)}`,
  };
}

/** Forward the product API's own SSE stream, translating its frames into ours.
 *  The product stream carries more than the page shows (stages, a trace, token
 *  counts); narrowing here rather than in the browser keeps internals off the wire. */
async function streamOurs(res, token, thread, message) {
  const turnId = `turn_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
  const upstream = await fetch(
    `${API_BASE}/api/v1/agents/${encodeURIComponent(AGENT_ID)}` +
      `/threads/${encodeURIComponent(thread)}/chat/stream`,
    {
      method: "POST",
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: JSON.stringify({ turn_id: turnId, message }),
    },
  );
  if (!upstream.ok || !upstream.body) {
    sse(res, "error", { message: "the answer service refused the turn", code: String(upstream.status) });
    return;
  }

  const reader = upstream.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    // SSE frames are separated by a blank line; a chunk boundary can fall anywhere, so
    // only whole frames are parsed and the tail is carried to the next read.
    let cut;
    while ((cut = buffer.indexOf("\n\n")) !== -1) {
      const frame = buffer.slice(0, cut);
      buffer = buffer.slice(cut + 2);
      const event = /^event:\s*(.+)$/m.exec(frame)?.[1]?.trim();
      const payload = /^data:\s*(.+)$/m.exec(frame)?.[1];
      if (!event || !payload) continue;
      let data;
      try {
        data = JSON.parse(payload);
      } catch {
        continue;
      }
      if (event === "delta" && data.delta) {
        sse(res, "delta", { text: data.delta });
      } else if (event === "error") {
        sse(res, "error", { message: data.message || "the turn failed", code: data.code || "error" });
      } else if (event === "complete") {
        const answer = data.response || {};
        sse(res, "done", {
          text: answer.message || "",
          citations: (answer.citations || []).filter(isFigure).map(asFigure),
        });
      }
    }
  }
}

/** A rival pane: the whole manual in context on every question. */
async function streamRival(res, which, message) {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key || !MANUAL_FILE_ID) {
    sse(res, "error", { message: "not connected", code: "unconfigured" });
    return;
  }
  const client = new Anthropic({ apiKey: key });
  try {
    // beta.messages, not messages: a document block that names a file_id is only
    // accepted under the files-api beta in this SDK version. Same beta as the upload
    // script — if one moves out of beta they both do.
    const stream = client.beta.messages.stream({
      betas: ["files-api-2025-04-14"],
      model: MODELS[which],
      max_tokens: 1024,
      system: SYSTEM,
      messages: [
        {
          role: "user",
          content: [
            {
              type: "document",
              source: { type: "file", file_id: MANUAL_FILE_ID },
              // One cache write shared by a burst of visitors. The 1h TTL is chosen
              // over the 5m default because traffic to a demo page is bursty and
              // sparse: at 5m nearly every visitor pays the write.
              cache_control: { type: "ephemeral", ttl: "1h" },
            },
            { type: "text", text: message },
          ],
        },
      ],
    });
    for await (const event of stream) {
      if (event.type === "content_block_delta" && event.delta?.type === "text_delta") {
        sse(res, "delta", { text: event.delta.text });
      }
    }
    const final = await stream.finalMessage();
    const text = final.content.filter((b) => b.type === "text").map((b) => b.text).join("");
    sse(res, "done", { text, citations: [] });
  } catch (err) {
    // The Haiku pane lives here: a 400 naming the page cap is the point of that pane,
    // so the API's own words are forwarded rather than replaced with our summary of
    // them. If the cap is ever raised this pane starts answering by itself.
    sse(res, "error", {
      message: err?.error?.error?.message || err?.message || "the model refused the request",
      code: String(err?.status || "error"),
    });
  }
}

/** Proxy one cited figure out of the product API, which the browser cannot reach. */
async function serveSource(req, res, sourceId) {
  const token = await productToken();
  const thread = readCookie(req, COOKIE);
  if (!token || !AGENT_ID || !thread) {
    res.status(404).end();
    return;
  }
  const upstream = await fetch(
    `${API_BASE}/api/v1/agents/${encodeURIComponent(AGENT_ID)}` +
      `/threads/${encodeURIComponent(thread)}/sources/${encodeURIComponent(sourceId)}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  if (!upstream.ok) {
    res.status(upstream.status === 404 ? 404 : 502).end();
    return;
  }
  res.setHeader("Content-Type", upstream.headers.get("content-type") || "application/octet-stream");
  // Figures are immutable once ingested, so the browser may keep one for the session.
  res.setHeader("Cache-Control", "private, max-age=3600");
  res.status(200).send(Buffer.from(await upstream.arrayBuffer()));
}

export default async function handler(req, res) {
  if (req.method === "GET") {
    const sourceId = new URL(req.url, "http://localhost").searchParams.get("source");
    if (!sourceId) {
      res.status(400).json({ error: "missing source" });
      return;
    }
    await serveSource(req, res, sourceId);
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ error: "method not allowed" });
    return;
  }
  if (overLimit(clientIp(req))) {
    res.status(429).json({ error: "too many questions, give it a minute" });
    return;
  }

  const body = typeof req.body === "string" ? JSON.parse(req.body || "{}") : req.body || {};
  const message = String(body.message || "").trim().slice(0, 2000);
  const which = String(body.model || "");
  if (!message || !(which === "ours" || which in MODELS)) {
    res.status(400).json({ error: "message and model are required" });
    return;
  }

  // WHY the thread is resolved BEFORE the stream opens: creating one sets a cookie, and a
  // header cannot be set once writeHead has run. It also turns a credential or thread-create
  // failure into a clean 503 the pane can report, rather than an error frame inside a
  // response that already claimed, with a 200, to be working.
  let token = null;
  let thread = null;
  if (which === "ours") {
    try {
      token = await productToken();
      if (!token || !AGENT_ID) throw new Error("unconfigured");
      thread = await ensureThread(req, res, token, String(body.user || ""));
    } catch (err) {
      console.error("try: ours setup", err);
      res.status(503).json({ error: "not connected" });
      return;
    }
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream; charset=utf-8",
    // no-transform and X-Accel-Buffering stop an intermediary from holding frames back
    // to fill a buffer. A buffered stream would report a TTFT that is the proxy's, not
    // the model's, which is the one number this page exists to show.
    "Cache-Control": "no-cache, no-transform",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });
  res.flushHeaders?.();

  try {
    if (which === "ours") await streamOurs(res, token, thread, message);
    else await streamRival(res, which, message);
  } catch (err) {
    sse(res, "error", { message: "the request could not be completed", code: "internal" });
    console.error("try:", which, err);
  }
  res.end();
}
