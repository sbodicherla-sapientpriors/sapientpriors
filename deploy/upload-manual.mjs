/**
 * Upload the MG Hector manual to the Anthropic Files API, once, and print its file_id.
 *
 * WHY this is a one-off script and not something /api/try does on demand: the PDF is
 * 10.2MB. Inlining it base64 costs ~13.6MB of request body per question per rival pane,
 * every time, and prompt caching does nothing about that — it caches tokens, not the
 * upload. Stored once, every request is a 40-character id.
 *
 * WHY the id goes in an env var rather than a file in the repo: it is account-scoped
 * state, not source. A redeploy must not be able to leave the code pointing at a file
 * that was never uploaded to the account it is running against.
 *
 *   ANTHROPIC_API_KEY=sk-... node deploy/upload-manual.mjs path/to/manual.pdf
 *   → set ANTHROPIC_MANUAL_FILE_ID to the printed id in the Vercel project
 *
 * Re-running uploads a SECOND copy and prints a new id; it is not idempotent. List with
 * `client.files.list()` before re-running if you are not sure one is already there.
 */

import { createReadStream } from "node:fs";
import { basename } from "node:path";
import Anthropic from "@anthropic-ai/sdk";

const path = process.argv[2];
if (!path) {
  console.error("usage: node deploy/upload-manual.mjs <path-to-pdf>");
  process.exit(2);
}
if (!process.env.ANTHROPIC_API_KEY) {
  console.error("ANTHROPIC_API_KEY is not set");
  process.exit(2);
}

// beta.files, not files: the Files API is still under the files-api-2025-04-14 beta in
// SDK 0.70, and the SDK sends that header for you from this namespace. When it moves to
// client.files this call and the betas array in api/try.js change together.
const client = new Anthropic();
const file = await client.beta.files.upload({
  file: await Anthropic.toFile(createReadStream(path), basename(path), {
    type: "application/pdf",
  }),
});

console.log(file.id);
