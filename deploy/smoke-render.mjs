/**
 * Check that the answer bubble turns the model's Markdown into DOM instead of printing it.
 *
 * WHY this is worth a test when the rest of the page is not: every other display bug fails
 * loudly — a pane stays empty, a clock sticks. This one fails quietly and looks like
 * carelessness: the answer arrives, it is correct, and it is full of "**" and "-". Real
 * answers from this manual come back with both, so the path is exercised constantly.
 *
 * No browser and no jsdom. The renderer only ever calls createElement / createTextNode /
 * appendChild / textContent, so twenty lines of stub cover it exactly, and a stub that has
 * to grow is a signal the renderer started doing something it should not.
 *
 *   node deploy/smoke-render.mjs
 */

import { readFile } from "node:fs/promises";
import { runInNewContext } from "node:vm";

function node(tag) {
  return {
    tag,
    children: [],
    _text: "",
    setAttribute() {},
    appendChild(child) {
      this.children.push(child);
      return child;
    },
    get textContent() {
      return this._text + this.children.map((c) => c.textContent).join("");
    },
    set textContent(value) {
      this._text = value;
      this.children = [];
    },
  };
}

globalThis.document = {
  createElement: (tag) => node(tag),
  createTextNode: (text) => ({ tag: "#text", children: [], textContent: text }),
};
// The module runs its mount loop on import; these keep it from throwing on the way past.
globalThis.window = { matchMedia: () => ({ matches: false, addEventListener() {} }) };
globalThis.requestAnimationFrame = () => {};
globalThis.localStorage = { getItem: () => null, setItem() {} };
globalThis.performance = { now: () => 0 };
globalThis.fetch = () => new Promise(() => {});
document.querySelector = () => null;
document.body = node("body");

/*
  Evaluated in a vm rather than imported. try-demo.js is a browser <script>, and the
  package is "type": "module" for the api/ functions, which would make Node read it as ESM
  and hand back none of its test hook. Running the source against an explicit CommonJS-ish
  frame keeps this test independent of how the package happens to be configured.
*/
const source = await readFile(new URL("../try-demo.js", import.meta.url), "utf8");
const frame = { module: { exports: {} }, document, window: globalThis.window,
                requestAnimationFrame, localStorage, performance, fetch };
frame.exports = frame.module.exports;
runInNewContext(source, frame);
const { renderAnswer } = frame.module.exports;
if (typeof renderAnswer !== "function") {
  console.error("try-demo.js did not expose renderAnswer — is the test hook still at the bottom?");
  process.exit(1);
}

let failures = 0;
function check(label, ok, detail = "") {
  console.log(`${ok ? "  ok  " : "FAIL  "}${label}${detail ? " — " + detail : ""}`);
  if (!ok) failures += 1;
}

function render(markdown) {
  const root = node("div");
  renderAnswer(root, markdown);
  return root;
}

// The exact shape a real answer came back in on 2026-09-15.
const REAL = [
  "There are several warning lights on the dashboard:",
  "",
  "- **Brake System:** The lamp illuminates after ignition and goes out once released.",
  "- **Airbag:** A fault is shown for 6 seconds.",
  "",
  "Refer to page 28 for the full table.",
].join("\n");

const out = render(REAL);
check("no ** survives into the rendered text", !out.textContent.includes("**"), out.textContent.slice(0, 60));
check("no bullet markers survive as text", !/(^|\n)\s*-\s/.test(out.textContent));
check("the bullet character is present instead", out.textContent.includes("•"));
check("the bold runs became strong elements", JSON.stringify(out).includes("strong"));
check("the words themselves are all still there", out.textContent.includes("Brake System") &&
  out.textContent.includes("Refer to page 28 for the full table."));

// Half-written bold, which is what every stream looks like partway through.
const partial = render("The **Brake Sys");
check("an unclosed ** renders as text rather than bolding the rest",
  partial.textContent === "The **Brake Sys", partial.textContent);

// Seen live: the model inlines its own memory ids into the prose. Occasional, so this is
// the only place that pins the behaviour — a live run cannot be relied on to reproduce it.
const LEAKED = "pull the strap [cde2c551489d41f090cccaec14de5928, e59e8bddf4154fb289fb88a00c320623] " +
  "and shake it [48d134753954492e8717ef2165bbe70a].";
const stripped = render(LEAKED).textContent;
check("inlined memory ids are stripped", !/[0-9a-f]{32}/.test(stripped), stripped);
check("the sentence survives the strip", stripped === "pull the strap and shake it.", stripped);
check("a half-arrived id does not flash on screen",
  render("pull the strap [cde2c551489d41f0").textContent === "pull the strap",
  render("pull the strap [cde2c551489d41f0").textContent);
check("ordinary brackets are left alone",
  render("see note [A] and [see page 12]").textContent === "see note [A] and [see page 12]",
  render("see note [A] and [see page 12]").textContent);

check("a heading loses its hashes", !render("## Warning lights").textContent.includes("#"));
check("plain prose is untouched", render("Just a sentence.").textContent === "Just a sentence.");
check("an empty answer does not throw", render("").textContent === "");

console.log(`\n${failures} failure(s)`);
process.exit(failures ? 1 : 0);
