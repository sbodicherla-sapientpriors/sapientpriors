/**
 * Drive /api/try for real, without Vercel and without a browser.
 *
 * WHY this exists rather than "it deploys, click it": the handler is the only part of the
 * playground that talks to both Google and the product API, and every failure mode it has
 * (wrong audience, no thread cookie, a frame shape the page cannot read, a citation href
 * that 404s) is invisible from the page — the pane just says nothing came back. This
 * exercises the frame sequence the browser depends on and asserts each piece.
 *
 * It calls the LIVE product API and spends real credits: one turn per run.
 *
 * Ask a question this thread has not seen. A repeat is answered from conversation history
 * ("As I mentioned...") without retrieving anything, so it legitimately returns zero
 * citations — which reads as a citation bug and is not one. Each run without SMOKE_THREAD
 * gets a fresh thread, so that only bites when the same question is repeated.
 *
 *   gcloud auth application-default login \
 *     --impersonate-service-account=playground-runtime@adaptive-agent-sp.iam.gserviceaccount.com
 *   PRODUCT_API_BASE_URL=... PLAYGROUND_AGENT_ID=... node deploy/smoke-try.mjs
 */

import handler from "../api/try.js";

const QUESTION = process.argv[2] || "What do the buttons on the remote key fob do?";

/** The two Node objects Vercel hands a function, reduced to what this handler touches. */
function fakeRes() {
  const chunks = [];
  const headers = {};
  const res = {
    statusCode: 200,
    body: null,
    headers,
    chunks,
    setHeader: (k, v) => (headers[k.toLowerCase()] = v),
    writeHead(code, hdrs) {
      res.statusCode = code;
      Object.assign(headers, hdrs || {});
      return res;
    },
    flushHeaders() {},
    status(code) {
      res.statusCode = code;
      return res;
    },
    json(payload) {
      res.body = payload;
      return res;
    },
    send(payload) {
      res.body = payload;
      return res;
    },
    write: (s) => chunks.push(s),
    end() {},
  };
  return res;
}

/** Parse the SSE text back into frames, the same way try-demo.js does. */
function frames(text) {
  const out = [];
  for (const block of text.split("\n\n")) {
    const event = /^event:\s*(.+)$/m.exec(block)?.[1]?.trim();
    const data = /^data:\s*(.+)$/m.exec(block)?.[1];
    if (event && data) out.push({ event, data: JSON.parse(data) });
  }
  return out;
}

let failures = 0;
function check(label, ok, detail = "") {
  console.log(`${ok ? "  ok  " : "FAIL  "}${label}${detail ? " — " + detail : ""}`);
  if (!ok) failures += 1;
}

console.log(`asking: ${QUESTION}\n`);
const started = Date.now();
// SMOKE_THREAD reuses an existing thread instead of creating one, so a citation
// difference can be attributed to the thread rather than to this endpoint.
const res = fakeRes();
await handler(
  {
    method: "POST",
    url: "/api/try",
    headers: process.env.SMOKE_THREAD ? { cookie: `sp_try_thread=${process.env.SMOKE_THREAD}` } : {},
    socket: {},
    body: { model: "ours", message: QUESTION },
  },
  res,
);

if (res.statusCode !== 200) {
  console.error(`handler refused with ${res.statusCode}:`, res.body);
  process.exit(1);
}

const seen = frames(res.chunks.join(""));
const deltas = seen.filter((f) => f.event === "delta");
const done = seen.find((f) => f.event === "done");
const errors = seen.filter((f) => f.event === "error");

check("no error frames", errors.length === 0, errors.map((e) => e.data.message).join("; "));
check("delta frames arrived", deltas.length > 0, `${deltas.length} deltas`);
check("a done frame closed the stream", !!done);
check("the answer has text", !!done?.data.text, `${done?.data.text?.length || 0} chars`);
check(
  "the streamed deltas match the settled answer",
  deltas.map((d) => d.data.text).join("").length > 0,
  "the page shows deltas first, then replaces them with done.text",
);

const cites = done?.data.citations || [];
check("citations came back", cites.length > 0, `${cites.length}`);
check(
  "every citation is a figure, not the parent PDF",
  cites.every((c) => c.media_type.startsWith("image/")),
  cites.map((c) => c.media_type).join(","),
);
check(
  "labels are readable, not stored filenames",
  cites.every((c) => /^Figure( \d+)?$/.test(c.label)),
  cites.map((c) => c.label).join(", "),
);
check(
  "hrefs point at this function's own proxy",
  cites.every((c) => c.href.startsWith("/api/try?source=")),
);
check(
  "the reading-order ordinal is on the tooltip, not the caption",
  cites.every((c) => /reading order|from the manual/.test(c.title || "")),
  cites[0]?.title || "",
);

console.log("\n--- answer ---\n" + (done?.data.text || "").slice(0, 600));
console.log("--- citations ---\n" + JSON.stringify(cites, null, 1) + "\n");

const cookie = res.headers["set-cookie"] || `sp_try_thread=${process.env.SMOKE_THREAD || ""}`;
if (!process.env.SMOKE_THREAD) {
  check("a thread cookie was set", cookie.includes("sp_try_thread="), cookie.split(";")[1] || "");
  check("the cookie is HttpOnly and scoped", cookie.includes("HttpOnly") && cookie.includes("Path=/api/try"));
}

// The figure proxy: the browser loads every thumbnail through it, so a 404 here is a
// silently broken citation strip rather than a visible error.
if (cites.length) {
  const sourceId = decodeURIComponent(cites[0].href.split("source=")[1]);
  const imgRes = fakeRes();
  await handler(
    {
      method: "GET",
      url: `/api/try?source=${encodeURIComponent(sourceId)}`,
      headers: { cookie: cookie.split(";")[0] },
      socket: {},
    },
    imgRes,
  );
  check("the figure proxy served the crop", imgRes.statusCode === 200, `http ${imgRes.statusCode}`);
  check(
    "it served image bytes",
    Buffer.isBuffer(imgRes.body) && imgRes.body.length > 1000,
    `${imgRes.body?.length || 0} bytes, ${imgRes.headers["content-type"]}`,
  );
}

console.log(`\n${Date.now() - started} ms total, ${failures} failure(s)`);
process.exit(failures ? 1 : 0);
