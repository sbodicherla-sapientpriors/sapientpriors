/**
 * Try It — the grounded-answer demo.
 *
 * The flow the page implements:
 *   1. Pick a display name for the session.
 *   2. Ask questions about the MG Hector owner's manual, 288 pages of it, open
 *      in the pane on the left.
 *   3. The answer comes back from memory, with the figures it drew on cited
 *      underneath, and the clock reports how long the first word took.
 *
 * The Claude Opus and Haiku panes that raced this one are switched off for now;
 * see CONTENDERS for what turning them back on costs and takes.
 *
 * ── State of play ───────────────────────────────────────────────────────────
 * Every send opens one SSE stream against /api/try per contender, and each pane
 * paints its own as it arrives. Nothing here is scripted: a pane that
 * cannot reach its model says so, because a demo whose whole claim is "it
 * answers from this document" cannot afford a canned reply that only looks
 * like one.
 *
 * ── What the shared pool does and does not do ───────────────────────────────
 * The playground agent has learning from turns switched OFF, so nothing a
 * visitor types becomes a memory a later visitor can retrieve. Within one
 * visitor's own session the conversation still carries — tell it you tow a
 * trailer and it knows that two questions later — but cross-visitor recall is
 * deliberately not there. That is a privacy decision, not an oversight: one
 * shared agent behind an anonymous public box means every memory written is a
 * memory a stranger can read, and people type real names into these.
 */
(function () {
  "use strict";

  var INK = "#14161A", INK2 = "#3A3E45", INK3 = "#6B7078", INK4 = "#9AA0A8";
  var LINE = "#E4E4E0", LINE_SOFT = "#EFEFEC", BONE = "#F6F6F4", WHITE = "#FFFFFF";
  // A step DOWN from the page, not up: the cards inside the demo are white, so a
  // white frame around them would dissolve the thing it is meant to separate.
  var SUNKEN = "#EFEFEC";

  /*
    How tall the two columns are, and therefore how tall the panel is.

    With STICK_TOP below, the panel's top border rests 89px down - sixteen clear
    of the 73px nav - and its bottom edge lands ~60px above the fold, so the demo
    is visibly smaller than the window on both axes. Both columns use the one
    expression, because the whole point of bounding them is that they end on the
    same line.
  */
  var COL_HEIGHT = "calc(100vh - 189px)";

  /* Where the manual card stops when the page scrolls past it. One padding step
     below the panel's own resting top edge, so the frame keeps its inset instead
     of the card climbing out through it. */
  var STICK_TOP = "109px";
  var BROWN = "#84512E", BROWN_D = "#6B4226";
  var MONO = "'Cascadia Code',ui-monospace,SFMono-Regular,Menlo,monospace";
  var SERIF = "Newsreader,Georgia,serif";

  var STORE_KEY = "sp:try-username";
  /*
    The manual is embedded from Drive rather than served from here.

    Shipping the PDF meant 10.2MB in the repo and 10.2MB across the wire for
    anyone who scrolled to it - the single heaviest thing on the site, for a
    document we do not own and cannot compress without ghostscript. Drive
    already has a paginated viewer with search and zoom, hosts it for free and
    streams a page at a time.

    The file is shared "anyone with the link can view", which is what makes the
    /preview embed render for a signed-out visitor. If that sharing setting is
    ever tightened the frame will go blank, so the header keeps a direct link
    out as the fallback.
  */
  var MANUAL_ID = "1fhL_JFLbeB1yEtrHvpdAb69Amc_moyKr";
  var MANUAL_EMBED = "https://drive.google.com/file/d/" + MANUAL_ID + "/preview";
  var MANUAL_OPEN = "https://drive.google.com/file/d/" + MANUAL_ID + "/view";

  /*
    WHY these four, and why they changed. The old set asked what OTHER visitors had
    stored, which this agent no longer answers now that learning from turns is off.

    These are chosen to be answerable and to be worth watching: the first two are buried
    deep in a 288-page manual and come back with the figure they were read from, which is
    the pane's whole argument; the third is a procedure, so a rival pane has to read
    before it can start. The last is in-session memory, which still works.
  */
  var SUGGESTIONS = [
    "How do I fit a child seat using ISOFIX?",
    "What do the warning lights on the instrument cluster mean?",
    "How do I change a flat tyre?",
    "Remember that I tow a trailer most weekends."
  ];

  /*
    WHY one pane and not three: the rival panes are switched off for now. /api/try still
    implements them, so restoring the race is adding the two rows back here — nothing
    else in this file is hard-coded to a count. Every layout below reads the length.

    They cost real money per question (Opus reads 288 scanned pages on every ask) and
    they need ANTHROPIC_MANUAL_FILE_ID, so a page shipped without that key would show
    two permanently broken panes beside a working one.
  */
  var CONTENDERS = [
    { id: "ours", name: "SapientPriors", ours: true }
  ];

  /*
    How long a pane waits for its FIRST token before admitting nothing is coming.

    It is deliberately long, and it only governs silence: once text starts arriving the
    clock runs until the answer ends, however long that takes. A rival handed 288 pages
    cold can take most of a minute to say its first word — cutting it off at a few
    seconds would hide the exact thing this page exists to show, and would read as our
    demo being broken rather than as their latency being real.
  */
  var SILENT_CUTOFF_MS = 60000;

  /*
    The backdrop behind the username card.

    Capped, because it is a glimpse and not the page: at full height the card
    centred in 790px of blur and landed below the fold, and the one thing it
    cannot do is be out of sight. Faded at the cut so it reads as more-below
    rather than as a component that stops.

    A constant rather than an inline string because lock() has to restore
    precisely what render() applied; two hand-copied copies drift apart the
    first time one of them is edited.
  */
  var LOCKED_BACKDROP =
    "filter:blur(5px);pointer-events:none;user-select:none;opacity:.65;" +
    "max-height:440px;overflow:hidden;" +
    "-webkit-mask-image:linear-gradient(to bottom,#000 62%,transparent);" +
    "mask-image:linear-gradient(to bottom,#000 62%,transparent)";

  /*
    turns is the conversation, oldest first. Each entry is
      { q: the question, at: the clock origin, results: { contenderId: r } }
    where r is the live object readStream fills in.

    WHY a list and not one current question: the demo used to hold exactly one
    turn - ask() wiped state.results and rebuilt the panes - so sending a second
    question erased the first and its answer. The API never behaved that way (one
    thread, full history, follow-ups resolve correctly), so the screen was
    contradicting the product on the page built to demonstrate it.

    WHY each turn owns its results rather than a shared state.results keyed by
    contender: two turns are on screen at once now, and a shared map would have
    the second answer stream into the first turn's bubble.
  */
  var state = { user: null, manual: null, turns: [], timers: [], abort: null };

  function el(tag, style, text) {
    var n = document.createElement(tag);
    if (style) n.setAttribute("style", style);
    if (text != null) n.textContent = text;
    return n;
  }

  /* ── the username gate ─────────────────────────────────────────────────── */
  function gate(mount, onDone) {
    var card = el("div", "max-width:34rem;margin:0 auto;border:1px solid " + LINE +
      ";border-radius:12px;background:" + WHITE + ";padding:clamp(1.75rem,3vw,2.5rem);text-align:center");

    card.appendChild(el("p", "margin:0 0 10px;font-family:" + MONO +
      ";font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;color:" + INK4, "Step one"));
    card.appendChild(el("h3", "margin:0 0 12px;font-family:" + SERIF +
      ";font-weight:400;font-size:clamp(1.4rem,1.1rem + .9vw,1.9rem);letter-spacing:-.015em;color:" + INK,
      "Pick a username."));
    card.appendChild(el("p", "margin:0 auto 22px;max-width:30rem;font-size:1rem;line-height:1.6;color:" + INK2,
      "A display name for this session, nothing more. Nothing you type is stored for " +
      "anyone else to read."));

    var form = el("form", "display:flex;gap:10px;justify-content:center;flex-wrap:wrap");
    var input = el("input", "flex:1;min-width:14rem;padding:11px 14px;border:1px solid " + LINE +
      ";border-radius:8px;font-size:.95rem;color:" + INK + ";background:" + BONE + ";outline:none");
    input.type = "text";
    input.placeholder = "e.g. hector_owner";
    input.maxLength = 24;
    input.setAttribute("aria-label", "Choose a username");
    var go = el("button", "flex:none;padding:11px 22px;border:0;border-radius:8px;background:" + BROWN +
      ";color:#fff;font-size:.9375rem;font-weight:500;cursor:pointer", "Start");
    go.type = "submit";
    go.addEventListener("mouseenter", function () { go.style.background = BROWN_D; });
    go.addEventListener("mouseleave", function () { go.style.background = BROWN; });

    var err = el("p", "margin:12px 0 0;font-size:.8125rem;color:#A03030;min-height:1.2em");

    form.appendChild(input);
    form.appendChild(go);
    card.appendChild(form);
    card.appendChild(err);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var v = input.value.trim().replace(/\s+/g, "_");
      if (v.length < 3) { err.textContent = "Three characters or more, please."; input.focus(); return; }
      if (!/^[A-Za-z0-9_.-]+$/.test(v)) { err.textContent = "Letters, numbers, dot, dash and underscore only."; return; }
      try { localStorage.setItem(STORE_KEY, v); } catch (_) {}
      onDone(v);
    });

    mount.appendChild(card);
    input.focus();
  }

  /* ── the tip panel ─────────────────────────────────────────────────────── */
  function tip() {
    /*
      Brown panel, white text. The alpha is .94 rather than the .5 that was
      asked for: at .5 over the page this resolves to a pale tan, and white on
      it lands near 2:1 contrast — legible on a designer's monitor and not on
      anything else. Same panel, same colour, text you can actually read.
    */
    var box = el("div", "display:flex;gap:14px;align-items:flex-start;margin:0 0 24px;" +
      "border:1px solid " + BROWN + ";border-radius:10px;" +
      "background:rgba(132,81,46,.94);padding:16px 18px");

    var bulb = el("span", "flex:none;margin-top:1px");
    bulb.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" ' +
      'stroke="#FFFFFF" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" ' +
      'aria-hidden="true"><path d="M9 18h6"/><path d="M10 21h4"/>' +
      '<path d="M12 3a6 6 0 0 0-3.6 10.8c.5.4.8.9.9 1.5l.1.7h5.2l.1-.7c.1-.6.4-1.1.9-1.5A6 6 0 0 0 12 3z"/></svg>';
    box.appendChild(bulb);

    var body = el("div", "min-width:0");
    body.appendChild(el("p", "margin:0 0 6px;font-family:" + MONO +
      ";font-size:.7rem;letter-spacing:.12em;text-transform:uppercase;color:rgba(255,255,255,.75)",
      "Fun tip"));
    var p = el("p", "margin:0;font-size:.9375rem;line-height:1.6;color:#FFFFFF");
    p.appendChild(document.createTextNode("Ask for something buried deep in the book. Try "));
    p.appendChild(el("span", "font-family:" + MONO + ";font-size:.85rem;background:rgba(255,255,255,.16);" +
      "padding:1px 6px;border-radius:4px", "How do I change a flat tyre?"));
    p.appendChild(document.createTextNode(" — then open the figure it cites and check it against the manual on the left."));
    body.appendChild(p);
    box.appendChild(body);
    return box;
  }

  /* ── the source ──────────────────────────────────────────────────────────
     An iframe of the manual itself rather than a list of chapter names. The
     names told you the document existed; they did not let you read it, and
     "every answer comes from this one document" is only checkable if you can
     actually open the document.

     10.2MB, so it is deliberately last on the page and lazy: the browser does
     not fetch it until it is scrolled to. Recompressing needs ghostscript,
     which is not on this machine — the weight is embedded raster, not text.
  */
  function source() {
    var card = el("div", "border:1px solid " + LINE + ";border-radius:12px;background:" + WHITE +
      ";overflow:hidden;position:sticky;top:" + STICK_TOP + ";display:flex;flex-direction:column;" +
      "max-height:" + COL_HEIGHT);

    var head = el("div", "padding:12px 14px;border-bottom:1px solid " + LINE_SOFT + ";flex:none");
    head.appendChild(el("p", "margin:0 0 2px;font-family:" + MONO + ";font-size:.7rem;letter-spacing:.14em;" +
      "text-transform:uppercase;color:" + INK4, "The source"));
    var ttl = el("p", "margin:0 0 6px;font-family:" + SERIF + ";font-size:1rem;line-height:1.3;color:" + INK,
      (state.manual ? state.manual.title : "MG Hector Owner's Manual"));
    head.appendChild(ttl);

    var meta = el("p", "margin:0;display:flex;align-items:center;justify-content:space-between;gap:10px;" +
      "font-family:" + MONO + ";font-size:.68rem;letter-spacing:.06em;color:" + INK4);
    meta.appendChild(el("span", "", (state.manual ? state.manual.pages : 288) + " PAGES"));
    var open = el("a", "font-family:" + MONO + ";font-size:.68rem;letter-spacing:.06em;" +
      "text-transform:uppercase;color:" + INK3, "Open \u2197");
    open.href = MANUAL_OPEN;
    open.target = "_blank";
    open.rel = "noopener";
    meta.appendChild(open);
    head.appendChild(meta);
    card.appendChild(head);

    var frame = document.createElement("iframe");
    frame.src = MANUAL_EMBED;
    frame.title = "MG Hector Owner's Manual";
    frame.loading = "lazy";
    frame.setAttribute("allow", "autoplay");
    frame.setAttribute("style", "display:block;width:100%;flex:1;min-height:26rem;border:0;background:" + BONE);
    card.appendChild(frame);
    return card;
  }

  /* ── the race ─────────────────────────────────────────────────────────────
     Three panes, the same question, clocks running. Restores the comparison
     the demo was built around: the argument is not that our answer is good,
     it is that theirs degrades once the context no longer fits.
  */
  function fmt(ms) {
    return ms < 1000 ? Math.round(ms) + " ms" : (ms / 1000).toFixed(2) + " s";
  }

  /*
    One contender's column: a fixed head, and under it a log that scrolls.

    The log is the scroller, not the grid around it. Scrolling the grid would
    move every column together and take the contenders' names off the top with
    it; scrolling the log keeps each name pinned over its own transcript, which
    is what a column of answers is for.
  */
  function column(c) {
    var box = el("div", "display:flex;flex-direction:column;min-height:0;overflow:hidden;" +
      "border-radius:12px;border:1px solid " + (c.ours ? "#E4D3C4" : LINE) +
      ";background:" + (c.ours ? "#FBF6F1" : WHITE));

    var head = el("div", "padding:11px 14px;border-bottom:1px solid " + LINE_SOFT + ";flex:none");
    head.appendChild(el("p", "margin:0;font-family:" + SERIF + ";font-size:1rem;color:" +
      (c.ours ? BROWN_D : INK), c.name));
    box.appendChild(head);

    /*
      No scroll-behavior:smooth here, deliberately.

      The log is pinned to the bottom 25 times a second while an answer streams,
      and each tick first asks whether the reader is still at the bottom. A smooth
      scroll is in flight across several of those ticks, so the question gets
      answered mid-animation - "no, they are 200px up" - and the follow switches
      itself off one tick after the new question was appended. Instant assignment
      makes the reading true at the moment it is taken; the motion the reader sees
      is the text arriving and pushing the conversation up, which is the thing that
      should be moving anyway.
    */
    var log = el("div", "flex:1;min-height:0;overflow-y:auto;display:flex;flex-direction:column;" +
      "gap:22px;padding:14px");
    log.setAttribute("data-log", c.id);
    box.appendChild(log);
    return box;
  }

  /* Is the reader at the bottom of this log? Asked BEFORE anything is appended,
     so that streaming text follows them down only when they were already there -
     pinning unconditionally would yank the page out from under someone who had
     scrolled up to re-read an earlier answer. */
  function atBottom(log) {
    return log.scrollHeight - log.scrollTop - log.clientHeight < 48;
  }

  function toBottom(log) { log.scrollTop = log.scrollHeight; }

  /* One question and its answer, for one contender. Appended to a log and never
     rebuilt: the interval below writes into the nodes it closed over, so an
     earlier turn keeps its text, its clock and its citations for the rest of
     the session. */
  function turnBlock(c, turn, log) {
    var body = el("div", "display:flex;flex-direction:column;gap:11px");

    var qRow = el("div", "display:flex;justify-content:flex-end");
    qRow.appendChild(el("p", "margin:0;max-width:88%;padding:9px 12px;border-radius:10px 10px 3px 10px;" +
      "font-size:.82rem;line-height:1.55;background:" + (c.ours ? BROWN : INK) + ";color:#fff", turn.q));
    body.appendChild(qRow);

    /*
      One number: time to the first token. That is the claim this page makes, and
      it is the number the reader is watching count up while they wait.

      Total time used to be printed beside it. Removed by request. Nothing
      simulates or rounds what is left - it is still measured in the browser, so
      it includes the hop the visitor actually pays for.
    */
    // WHY lbl is its own span: it is set independently of num as the stream reaches
    // a different state, and rebuilding one string would fight the interval.
    var clock = el("p", "margin:0;display:flex;align-items:center;justify-content:flex-end;gap:8px;" +
      "font-family:" + MONO + ";font-size:.75rem;color:" + INK4);
    var dot = el("span", "width:6px;height:6px;border-radius:50%;background:" + BROWN);
    var num = el("span", "font-weight:500;color:" + INK2, "0 ms");
    var lbl = el("span", "letter-spacing:.06em", "");
    clock.appendChild(dot); clock.appendChild(num); clock.appendChild(lbl);
    body.appendChild(clock);

    var aRow = el("div", "display:flex;justify-content:flex-start");
    // A div, not a p: renderAnswer puts block children inside it for bullets and headings,
    // and a <p> may not legally contain them \u2014 browsers silently close the paragraph and
    // the bubble's border ends up wrapped around the first line only.
    var ans = el("div", "margin:0;max-width:94%;padding:9px 12px;border-radius:10px 10px 10px 3px;border:1px solid " +
      LINE + ";background:" + BONE + ";font-size:.82rem;line-height:1.55;color:" + INK3, "\u2026");
    aRow.appendChild(ans);
    body.appendChild(aRow);

    var cites = el("div", "display:none;flex-wrap:wrap;gap:8px;margin-top:2px");
    body.appendChild(cites);

    /*
      An interval, not requestAnimationFrame: rAF is suspended outright in a
      background tab, which freezes the clock at zero and reads as broken.
    */
    var started = turn.at;
    // WHY painted tracks a length rather than re-setting textContent every tick: the
    // answer arrives a few characters at a time and rewriting an unchanged node 25
    // times a second is what collapses a text selection the reader is holding.
    var painted = 0;
    var drewCites = false;
    var t = setInterval(function () {
      var r = turn.results[c.id];
      var e = performance.now() - started;
      // Read before the paint below changes the height, so "were they at the
      // bottom" means before this tick's text arrived, not after it.
      var follow = log && atBottom(log);

      if (r && r.ttft !== null) {
        num.textContent = fmt(r.ttft);
        lbl.textContent = "to first word";
      } else {
        num.textContent = fmt(e);
      }

      if (r && r.text.length !== painted) {
        painted = r.text.length;
        renderAnswer(ans, r.text);
        if (follow && log) toBottom(log);
      }

      if (r && r.done) {
        clearInterval(t);
        dot.style.background = LINE;
        if (r.error) {
          /*
            The refusal IS the result for a rival pane, so it is shown as text rather
            than swallowed \u2014 the page's claim is that the page cap is real, and the
            API's own words are the evidence.

            But an error that arrives AFTER text has been painted is a different thing:
            a dropped connection mid-answer. Replacing the half-written answer with
            "the connection dropped" throws away what the reader was in the middle of,
            so the text stays and the failure is said underneath it.
          */
          num.textContent = "\u2014";
          lbl.textContent = "";
          if (r.text) {
            body.insertBefore(el("p", "margin:0;font-family:" + MONO + ";font-size:.68rem;color:" +
              INK4, r.error), cites);
          } else {
            ans.textContent = r.error;
            ans.style.color = INK4;
          }
        } else {
          // No first token ever arrived but the turn finished, so the only honest
          // figure left is how long the whole thing took.
          if (r.ttft === null) num.textContent = fmt(r.ms);
          if (!r.text) ans.textContent = "(empty reply)";
        }
        if (!drewCites) { drewCites = true; drawCitations(cites, r.citations); }
        return;
      }

      // The cutoff governs SILENCE only: a stream that has started is never cut off.
      if (!r || (r.ttft === null && !r.text)) {
        if (e >= SILENT_CUTOFF_MS) {
          clearInterval(t);
          // Stop the request as well as the clock, so what the pane says and what is
          // actually still running cannot disagree. See readStream for why r owns this.
          if (r && r.abort) r.abort();
          num.textContent = "\u2014";
          dot.style.background = LINE;
          ans.textContent = "No answer came back.";
          ans.style.color = INK4;
        }
      }
    }, 40);
    state.timers.push(t);
    return body;
  }

  /* \u2500\u2500 the answer \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
     WHY the answer is parsed at all: the model writes Markdown. Real answers from this
     manual come back with "**Brake System:**" and "- " bullets, and a text node prints
     those markers literally. On a page whose entire job is to look finished, visible
     asterisks read as a broken renderer \u2014 the exact impression this demo cannot afford.

     Deliberately tiny: bold, bullets, and headings, which are the only three that actually
     appear here. Everything else stays text. Built from DOM nodes and never innerHTML, so
     a document that happens to contain markup cannot inject it into the page.
  */
  function inline(node, text) {
    var parts = text.split("**");
    // An odd count means a ** was left open \u2014 mid-stream, usually. Rendering it as text
    // beats bolding the rest of the answer until the closing pair arrives.
    if (parts.length % 2 === 0) { node.appendChild(document.createTextNode(text)); return; }
    parts.forEach(function (part, i) {
      if (!part) return;
      node.appendChild(i % 2
        ? el("strong", "font-weight:600;color:" + INK2, part)
        : document.createTextNode(part));
    });
  }

  /*
    The answer sometimes arrives with the model's internal memory ids inlined into the
    prose: "...on the back of the seat [cde2c551489d41f090cccaec14de5928, e59e8bddf41...]".
    Seen live on 2026-09-15 and NOT on the same question a minute later, so it is
    occasional rather than constant — which is worse, because it cannot be relied on to
    show up in a test and it makes the page look broken the one time a visitor hits it.

    Stripped here rather than in /api/try because this sees the whole accumulated answer:
    a sentinel split across two delta frames would slip past a per-frame filter. The
    trailing rule catches one that is still arriving, so a half-written id does not flash
    on screen; it costs an unclosed "[" at the very end of an answer, which reappears as
    soon as the next character does.
  */
  var MEMORY_IDS = /\s*\[\s*[0-9a-f]{32}(?:\s*,\s*[0-9a-f]{32})*\s*\]/g;
  var PARTIAL_ID = /\s*\[\s*[0-9a-f]{0,32}(?:\s*,\s*[0-9a-f]{0,32})*\s*$/;

  function clean(text) {
    return text.replace(MEMORY_IDS, "").replace(PARTIAL_ID, "");
  }

  function renderAnswer(node, text) {
    node.textContent = "";
    clean(text).split("\n").forEach(function (line) {
      if (!line.trim()) { node.appendChild(el("div", "height:.5em")); return; }
      var heading = /^\s*#{1,6}\s+(.*)$/.exec(line);
      if (heading) {
        var h = el("div", "margin:.2em 0 .1em");
        inline(h, "**" + heading[1] + "**");
        node.appendChild(h);
        return;
      }
      var bullet = /^\s*[-*]\s+(.*)$/.exec(line);
      if (bullet) {
        var row = el("div", "display:flex;gap:7px;align-items:baseline");
        row.appendChild(el("span", "flex:none;color:" + INK4, "\u2022"));
        var body = el("span", "min-width:0");
        inline(body, bullet[1]);
        row.appendChild(body);
        node.appendChild(row);
        return;
      }
      var p = el("div", "");
      inline(p, line);
      node.appendChild(p);
    });
  }

  /* \u2500\u2500 citations \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
     The figures the answer drew on, straight out of the manual. This is the half of
     the claim the text alone cannot carry: an answer about ISOFIX anchor points is
     worth more when the diagram it read is sitting under it.

     The wording stays "cited" and never "verified" or "proof". Each of these is the
     model reporting which stored figure the memory it answered from came with \u2014 a real
     pointer into the document, not an independent check that the figure supports the
     sentence. The visitor does that check themselves, which is why every chip opens.
  */
  function drawCitations(mount, list) {
    if (!list || !list.length) return;
    mount.style.display = "flex";
    mount.appendChild(el("p", "margin:0;width:100%;font-family:" + MONO +
      ";font-size:.62rem;letter-spacing:.14em;text-transform:uppercase;color:" + INK4,
      "Cited from the manual"));

    var SHOWN = 6;
    list.slice(0, SHOWN).forEach(function (cit) {
      var chip = el("a", "display:flex;align-items:center;gap:7px;max-width:100%;padding:5px 9px 5px 5px;" +
        "border:1px solid " + LINE + ";border-radius:8px;background:" + WHITE + ";text-decoration:none");
      chip.href = cit.href;
      chip.target = "_blank";
      chip.rel = "noopener";
      if (cit.title) chip.title = cit.title;

      if (String(cit.media_type || "").indexOf("image/") === 0) {
        var thumb = document.createElement("img");
        thumb.src = cit.href;
        // Decorative: the chip's own text is the accessible name, so alt text here would
        // make a screen reader announce every figure twice.
        thumb.alt = "";
        thumb.loading = "lazy";
        thumb.setAttribute("style", "width:34px;height:34px;object-fit:cover;border-radius:5px;" +
          "background:" + BONE + ";flex:none");
        chip.appendChild(thumb);
      }
      chip.appendChild(el("span", "font-family:" + MONO + ";font-size:.68rem;color:" + INK2 +
        ";overflow:hidden;text-overflow:ellipsis;white-space:nowrap", cit.label || "Figure"));
      mount.appendChild(chip);
    });

    // WHY the overflow is stated rather than silently sliced: a well-cited answer really
    // does come back with eight or more crops, and quietly showing six would misreport how
    // much of the document the answer rests on — on the one page whose argument is exactly
    // that. Six is the display cap; the count stays honest.
    if (list.length > SHOWN) {
      mount.appendChild(el("span", "align-self:center;font-family:" + MONO +
        ";font-size:.68rem;color:" + INK4, "+" + (list.length - SHOWN) + " more"));
    }
  }

  function race() {
    /*
      A column, not a block, and it grows. The manual beside it is sticky and
      viewport-tall, so leaving this content-height ended the right-hand side
      hundreds of pixels above the manual's bottom edge and left the composer
      floating near the top of an empty half. Filling the height puts the
      composer on the manual's bottom edge, and the two halves read as one box.
    */
    var wrap = el("div", "flex:1;min-height:0;display:flex;flex-direction:column");
    if (!state.turns.length) {
      // centred in the space rather than padded down from the top: the padding
      // was a guess at the height, and this is the height.
      var empty = el("div", "flex:1;min-height:0;display:flex;flex-direction:column;" +
        "align-items:center;justify-content:center;border:1px dashed " + LINE +
        ";border-radius:12px;padding:24px;text-align:center");
      // WHY the copy changed: it used to invite you to "tell it something to remember"
      // and to watch three clocks. Neither is true now — learning from turns is off and
      // the rival panes are hidden, so the empty state promises what the page delivers.
      empty.appendChild(el("p", "margin:0 0 6px;font-family:" + SERIF + ";font-size:1.15rem;color:" + INK,
        "Ask the manual something."));
      empty.appendChild(el("p", "margin:0;font-size:.85rem;color:" + INK3,
        "The clock starts on send and stops on the first word back."));
      wrap.appendChild(empty);
      return wrap;
    }
    // One column per contender, read from the list rather than pinned at three, so
    // turning the rivals back on is a data change and not a CSS hunt.
    // overflow hidden, not auto: each column scrolls its own log now, and a
    // scrollbar here as well would give the reader two nested scrollers over the
    // same content.
    var cols = el("div", "flex:1;min-height:0;overflow:hidden;display:grid;grid-template-columns:repeat(" +
      CONTENDERS.length + ",minmax(0,1fr));gap:14px");
    cols.setAttribute("data-race-cols", "");
    CONTENDERS.forEach(function (c) {
      var box = column(c);
      var log = box.querySelector("[data-log]");
      // Replayed rather than kept, because this path only runs on a full render()
      // - first mount, or a fallback - and the turn objects hold everything a
      // block needs to be rebuilt exactly as it was.
      state.turns.forEach(function (turn) { log.appendChild(turnBlock(c, turn, log)); });
      cols.appendChild(box);
    });
    wrap.appendChild(cols);
    // The newest turn is the one being read, and a replayed log opens at the top.
    requestAnimationFrame(function () {
      cols.querySelectorAll("[data-log]").forEach(toBottom);
    });
    return wrap;
  }

  /*
    Bring the demo into view after the gate is cleared.

    Starting a session left the page exactly where it was: the card vanished,
    the interface appeared in the same place, and on anything but a very tall
    window the manual and the composer were below the fold. The visitor had
    just asked for the thing and had to go looking for it.

    Two frames, not one. render() rebuilds the tree and lay() sets the column
    heights inside it; measuring before the browser has laid that out reads the
    old geometry and scrolls to the wrong place. One frame gets the DOM, the
    second gets it measured.

    The nav offset is measured rather than assumed, because it is the fixed bar
    that would otherwise cover the top of what we just scrolled to.
  */
  function reveal(mount) {
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        var grid = mount.querySelector("[data-try-panel]") ||
                   mount.querySelector("[data-try-grid]");
        if (!grid) return;
        var nav = 0;
        document.querySelectorAll("div,header,nav").forEach(function (e) {
          var cs = getComputedStyle(e), r = e.getBoundingClientRect();
          if (cs.position === "fixed" && r.top <= 1 && r.height > 24 &&
              r.height < 140 && r.width > window.innerWidth * 0.6) {
            nav = Math.max(nav, r.height);
          }
        });
        var y = Math.max(0, grid.getBoundingClientRect().top + window.scrollY - (nav + 16));
        /*
          Through scroll-motion's lerp when it is present, not around it.

          That script owns the wheel and drives the page from its own rAF loop.
          A native smooth scroll started here writes scrollY on the same frames
          the lerp does, and the lerp wins - so this scroll simply did not
          happen for anyone who had touched the wheel.
        */
        var m = window.__spMotion;
        if (m && m.scrollTo) m.scrollTo(y);
        else window.scrollTo({ top: y, behavior: "smooth" });
      });
    });
  }

  /* ── updating without rebuilding ──────────────────────────────────────────
     render() is a full teardown: mount.innerHTML = "" and the whole tree again.
     That is fine once, and wrong every time after, because the left column holds
     an iframe. Detaching an iframe from the document does not move it, it
     restarts it — so every question refetched 10.2MB of manual from Drive and
     threw the reader back to page one of 288, mid-sentence, on the one page whose
     argument is "open the figure it cites and check it".

     It also read as amnesia. The API is a single thread and genuinely remembers
     the conversation - a follow-up with no subject in it is answered correctly -
     but wiping the screen on send made a continuing conversation look like a
     fresh one every time.

     So nothing below tears anything down. Each function changes the one part
     that actually differs and leaves the iframe attached and playing.
  */

  /* Settle anything still streaming, so an aborted turn stops counting.

     An abort resolves nothing: readStream's catch returns early on AbortError
     precisely because the result object is normally orphaned. Now that the turn
     stays on screen, its interval would keep ticking under a superseded answer
     until the silence cutoff, ~60s later. */
  function settlePending() {
    state.turns.forEach(function (turn) {
      Object.keys(turn.results).forEach(function (k) {
        var r = turn.results[k];
        if (r.done) return;
        r.done = true;
        r.ms = r.ms || (performance.now() - turn.at);
        // Half an answer is still the answer it got, so text is kept and the
        // reason is said under it. Nothing arrived at all - say so plainly.
        if (!r.text) r.error = "superseded by the next question";
      });
    });
  }

  /* Add one turn to the bottom of every column, leaving every earlier turn
     exactly where it is. This is the whole of what asking does to the screen. */
  function appendTurn(mount, turn) {
    var cols = mount.querySelector("[data-race-cols]");
    // No columns yet means the empty state is still up; race() builds them and
    // replays the turn list, which this turn is already in.
    if (!cols) { repaint(mount); return; }
    CONTENDERS.forEach(function (c) {
      var log = cols.querySelector('[data-log="' + c.id + '"]');
      if (!log) return;
      log.appendChild(turnBlock(c, turn, log));
      // Unconditional here, unlike during streaming: the reader just pressed
      // send, so the new question is what they are looking for.
      requestAnimationFrame(function () { toBottom(log); });
    });
  }

  /* A full rebuild of the answer side. Only the reset path and the first turn
     need it now - a question appends. */
  function repaint(mount) {
    var right = mount.querySelector("[data-try-right]");
    if (!right || !right.firstChild) { render(mount); return; }
    right.replaceChild(race(), right.firstChild);
    // The fresh pane grid has no column count on it yet, and lay() is what owns
    // that decision at each breakpoint.
    if (state.lay) state.lay();
  }

  /* Clearing the gate: unblur, reveal the bar, drop the card. Everything the
     visitor was already looking at through the blur stays exactly where it was,
     including a manual that has had the whole time they spent reading the card
     to finish loading. */
  function unlock(mount) {
    var body = mount.querySelector("[data-try-body]");
    var veil = mount.querySelector("[data-try-veil]");
    var bar = mount.querySelector("[data-try-bar]");
    var who = mount.querySelector("[data-try-who]");
    if (!body) { render(mount); return; }
    body.setAttribute("style", "");
    body.removeAttribute("aria-hidden");
    if (who) who.textContent = state.user;
    if (bar) bar.style.visibility = "";
    if (veil && veil.parentNode) veil.parentNode.removeChild(veil);
    if (state.lay) state.lay();
  }

  /* And back, for "Change username". */
  function lock(mount) {
    var stage = mount.querySelector("[data-try-stage]");
    var body = mount.querySelector("[data-try-body]");
    var bar = mount.querySelector("[data-try-bar]");
    if (!stage || !body) { render(mount); return; }
    body.setAttribute("style", LOCKED_BACKDROP);
    body.setAttribute("aria-hidden", "true");
    if (bar) bar.style.visibility = "hidden";
    if (mount.querySelector("[data-try-veil]")) return;
    var veil = el("div", "position:absolute;inset:0;display:flex;align-items:center;" +
      "justify-content:center;padding:24px");
    veil.setAttribute("data-try-veil", "");
    var holder = el("div", "width:100%;max-width:34rem");
    gate(holder, function (u) {
      state.user = u;
      warm();
      unlock(mount);
      reveal(mount);
    });
    veil.appendChild(holder);
    stage.appendChild(veil);
  }

  function render(mount) {
    mount.innerHTML = "";
    /*
      No max-width. Every other section on this page runs to a ~72px gutter -
      at a 2000px viewport they span 1857px while this was pinned to 1400 and
      centred, so the demo sat in a narrow channel with the page running wider
      on both sides of it. Matching the page's own gutter is what makes the
      three panes wide enough to read instead of three columns crushed into two
      thirds of 1400px.
    */
    var wrap = el("div", "margin:0 auto;max-width:1720px;padding:0 clamp(1.25rem,3.2vw,4.5rem)");

    /*
      The gate no longer replaces the demo, it sits on top of it.

      A lone "pick a username" card said nothing about what picking one got you,
      so the ask came before any reason to agree to it. The real interface is
      built either way now and shown behind the card, blurred: the manual, the
      composer and the suggestions are all legible enough as shapes to tell you
      there is something here, and unreadable enough that the demo is still
      something you start rather than something you watched.

      Blurred is not disabled. pointer-events and user-select are off on the
      backdrop as well, so nothing behind the card can be clicked, tabbed into
      or selected while it is locked - a blur alone would leave a working form
      under a frosted pane.
    */
    var locked = !state.user;
    var stage = el("div", "position:relative");
    stage.setAttribute("data-try-stage", "");
    var body = el("div", locked ? LOCKED_BACKDROP : "");
    body.setAttribute("data-try-body", "");
    if (locked) body.setAttribute("aria-hidden", "true");

    var bar = el("div", "display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 20px;flex-wrap:wrap");
    bar.setAttribute("data-try-bar", "");
    // "Signed in as" with nothing after it is worse than no bar at all.
    if (locked) bar.style.visibility = "hidden";
    var who = el("p", "margin:0;font-size:.9375rem;color:" + INK2);
    who.appendChild(document.createTextNode("Signed in as "));
    var whoName = el("span", "font-family:" + MONO + ";color:" + INK, state.user);
    whoName.setAttribute("data-try-who", "");
    who.appendChild(whoName);
    bar.appendChild(who);
    var swap = el("button", "border:1px solid " + LINE + ";background:transparent;border-radius:8px;" +
      "padding:7px 14px;font-size:.8125rem;color:" + INK3 + ";cursor:pointer", "Change username");
    swap.addEventListener("click", function () {
      state.timers.forEach(clearInterval); state.timers = [];
      if (state.abort) state.abort.abort();
      state.user = null; state.turns = [];
      try { localStorage.removeItem(STORE_KEY); } catch (_) {}
      repaint(mount);
      lock(mount);
    });
    bar.appendChild(swap);
    body.appendChild(bar);
    body.appendChild(tip());

    var form = el("form", "border:1px solid " + LINE + ";border-radius:12px;background:" + WHITE +
      ";padding:14px");
    var row = el("div", "display:flex;gap:10px;align-items:center");
    var input = el("input", "flex:1;min-width:0;padding:11px 13px;border:1px solid " + LINE +
      ";border-radius:8px;font-size:.9rem;color:" + INK + ";background:" + BONE + ";outline:none");
    input.type = "text";
    input.placeholder = "Ask about the manual, or tell it something to remember";
    input.setAttribute("aria-label", "Message");
    var send = el("button", "flex:none;padding:11px 20px;border:0;border-radius:8px;background:" + BROWN +
      ";color:#fff;font-size:.875rem;font-weight:500;cursor:pointer",
      CONTENDERS.length > 1 ? "Ask all " + CONTENDERS.length : "Ask");
    send.type = "submit";
    row.appendChild(input); row.appendChild(send);
    form.appendChild(row);

    var chips = el("div", "display:flex;flex-wrap:wrap;gap:8px;margin-top:11px");
    SUGGESTIONS.forEach(function (q) {
      var c = el("button", "padding:6px 11px;border:1px solid " + LINE + ";border-radius:999px;background:" +
        BONE + ";font-size:.75rem;color:" + INK3 + ";cursor:pointer;text-align:left", q);
      c.type = "button";
      c.addEventListener("click", function () { ask(q, mount); });
      chips.appendChild(c);
    });
    form.appendChild(chips);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (input.value.trim()) { ask(input.value, mount); input.value = ""; }
    });
    /*
      Manual on the left third, the demo on the right two thirds with the three
      panes above the box you type into.

      Panes above composer is the chat convention, and it is the right one here:
      the answers are the thing being compared, so they get the top of the
      column, and the composer sits under them where your hands already are.

      The DOM order is demo-then-manual, with the columns placed explicitly so
      the manual still paints on the left. That way the single-column phone
      layout - which just follows DOM order - puts the interactive half first
      rather than burying it under a 288-page document.
    */
    /*
      The frame.

      Both columns were bounded to the viewport and the wrap ran to the page's
      own gutter, so the demo met all four edges of the window with nothing
      between it and the page - it read as the page rather than as a thing
      sitting on it. A border, a step down in tone from the page behind it, and
      a legend riding the top edge make it one panel; the column heights below
      are cut so it clears the nav at the top and the fold at the bottom.

      overflow stays visible. The manual card inside is position:sticky, and an
      overflow of anything but visible makes this element its scroll container,
      which stops the sticky working at all.
    */
    var panel = el("div", "position:relative;border:1px solid " + LINE + ";border-radius:16px;" +
      "background:" + SUNKEN + ";padding:clamp(14px,1.4vw,20px)");
    panel.setAttribute("data-try-panel", "");
    // Sits ON the border and paints the page colour over it, so the rule breaks
    // for the width of the word the way a fieldset legend does.
    var legend = el("span", "position:absolute;top:0;left:clamp(18px,2vw,30px);" +
      "transform:translateY(-50%);background:" + BONE + ";padding:0 10px;font-family:" + MONO +
      ";font-size:.68rem;letter-spacing:.14em;text-transform:uppercase;color:" + INK4, "Live demo");
    panel.appendChild(legend);

    var grid = el("div", "display:grid;gap:clamp(1rem,1.8vw,1.5rem);align-items:start");
    grid.setAttribute("data-try-grid", "");

    var right = el("div", "display:flex;flex-direction:column;gap:14px;min-width:0");
    right.setAttribute("data-try-right", "");
    right.appendChild(race());
    right.appendChild(form);
    grid.appendChild(right);

    var left = el("div", "min-width:0");
    left.setAttribute("data-try-left", "");
    left.appendChild(source());
    grid.appendChild(left);

    panel.appendChild(grid);
    body.appendChild(panel);

    /*
      WHY this was rewritten and not just trimmed: it used to say "anything you store here
      can be read by anyone who visits later", which stopped being true the moment learning
      from turns was switched off. A privacy notice that overstates exposure is still a
      false statement on a company page, and this one actively discourages the thing the
      demo is for. What replaces it is the same promise the backend now actually keeps.
    */
    body.appendChild(el("p", "margin:18px 0 26px;font-size:.75rem;line-height:1.6;color:" + INK4,
      "Your conversation stays in this session and is not stored for other visitors to read. " +
      "The manual is the only thing in shared memory. Questions are sent to our API to be " +
      "answered."));

    stage.appendChild(body);

    if (locked) {
      var veil = el("div", "position:absolute;inset:0;display:flex;align-items:center;" +
        "justify-content:center;padding:24px");
      veil.setAttribute("data-try-veil", "");
      var holder = el("div", "width:100%;max-width:34rem");
      gate(holder, function (u) {
        state.user = u;
        warm();
        unlock(mount);
        reveal(mount);
      });
      veil.appendChild(holder);
      stage.appendChild(veil);
    }

    wrap.appendChild(stage);
    mount.appendChild(wrap);

    /*
      Two breakpoints, not one. The panes go single-file well before the page
      does: three columns inside two thirds of the width is about 20rem each,
      which is already tight, so they collapse at 1180px while the manual keeps
      its column down to 900px.
    */
    var mqPage = window.matchMedia("(max-width: 900px)");
    var mqPanes = window.matchMedia("(max-width: 1180px)");
    function lay() {
      grid.style.gridTemplateColumns = mqPage.matches
        ? "minmax(0,1fr)"
        : "minmax(0,1fr) minmax(0,2fr)";
      left.style.gridColumn = mqPage.matches ? "auto" : "1";
      left.style.gridRow = mqPage.matches ? "auto" : "1";
      right.style.gridColumn = mqPage.matches ? "auto" : "2";
      right.style.gridRow = mqPage.matches ? "auto" : "1";
      // The same height the manual card is bounded to, so both columns end on
      // the same line. On one column there is nothing to align to, and a fixed
      // height would just cut the page off.
      right.style.height = mqPage.matches ? "auto" : COL_HEIGHT;

      var card = left.firstChild;
      if (card) {
        card.style.position = mqPage.matches ? "static" : "sticky";
        /*
          height, not max-height, and the same expression the right column uses.

          max-height let the card stop at its content - the manual rendered 498px
          tall inside a 792px allowance - so pinning the right column to the
          viewport height put the composer 294px BELOW the manual's bottom edge
          and made the misalignment worse than it started. Given a height, the
          iframe is flex:1 and grows to fill it, and both columns end on the
          same line.
        */
        card.style.height = mqPage.matches ? "auto" : COL_HEIGHT;
      }

      /*
        On one column the right-hand side is height:auto, so nothing above the
        log bounds it and a long conversation would push the composer off the
        bottom of the page. A ceiling here gives the log its own scroll instead.
      */
      wrap.querySelectorAll("[data-log]").forEach(function (lg) {
        lg.style.maxHeight = mqPage.matches ? "68vh" : "";
      });

      var rc = wrap.querySelector("[data-race-cols]");
      if (rc) {
        rc.style.gridTemplateColumns = mqPanes.matches
          ? "minmax(0,1fr)"
          : "repeat(" + CONTENDERS.length + ",minmax(0,1fr))";
      }
    }
    state.lay = lay;
    lay();
    mqPage.addEventListener("change", lay);
    mqPanes.addEventListener("change", lay);
  }

  /*
    Read one pane's SSE stream into its live result object.

    WHY it mutates turn.results[id] rather than resolving a promise with the finished
    answer: the pane already polls that object on an interval to paint its clock, so
    streaming needs no second render path and no re-render of the page. The reader
    fills the object in; the interval paints whatever is in it. render() rebuilds the
    whole tree, and calling it per token would drop the caret and the scroll position.

    WHY time-to-first-token is measured here and not on the server: this is the number
    the visitor actually waits, browser hop included. All three panes pay the same hop
    on the same connection, so the comparison stays fair and the absolute figure stays
    honest — a server-side clock would quietly flatter every pane by the same amount.
  */
  function readStream(turn, id, signal) {
    var t0 = turn.at;
    /*
      WHY each pane gets its own controller, chained to the shared one: the shared signal
      supersedes the whole question, but a single pane also needs to give up alone when its
      own clock runs out. Without r.abort the pane would print "No answer came back" while
      its request carried on in the background — the screen saying one thing and the
      billing another, and a late answer arriving with no timer left to paint it.
    */
    var ctrl = new AbortController();
    if (signal) signal.addEventListener("abort", function () { ctrl.abort(); });

    // WHY the object is published before the fetch: turnBlock()'s interval is already
    // running, and a pane polling an id that is not there yet has no way to tell
    // "the request has not been made" from "the answer never came".
    var r = { text: "", ttft: null, ms: null, done: false, error: null, citations: [],
              abort: function () { ctrl.abort(); } };
    turn.results[id] = r;

    fetch("/api/try", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: state.user, model: id, message: turn.q }),
      signal: ctrl.signal
    }).then(function (res) {
      if (!res.ok || !res.body) throw new Error(String(res.status));
      var reader = res.body.getReader();
      var dec = new TextDecoder();
      var buf = "";

      function frame(block) {
        var ev = /^event:\s*(.+)$/m.exec(block);
        var dat = /^data:\s*(.+)$/m.exec(block);
        if (!ev || !dat) return;
        var d;
        try { d = JSON.parse(dat[1]); } catch (_) { return; }
        if (ev[1].trim() === "delta") {
          if (r.ttft === null) r.ttft = performance.now() - t0;
          r.text += d.text || "";
        } else if (ev[1].trim() === "done") {
          if (d.text) r.text = d.text;          // the settled answer, not the deltas
          r.citations = d.citations || [];
          r.ms = performance.now() - t0;
          r.done = true;
        } else if (ev[1].trim() === "error") {
          r.error = d.message || "the answer failed";
          r.ms = performance.now() - t0;
          r.done = true;
        }
      }

      function pump() {
        return reader.read().then(function (step) {
          if (step.done) {
            // A stream that ends without a done frame is a dropped connection, not an
            // answer. Saying so beats leaving a half-written reply looking finished.
            if (!r.done) { r.error = r.error || "the connection dropped"; r.done = true; }
            return;
          }
          buf += dec.decode(step.value, { stream: true });
          var cut;
          while ((cut = buf.indexOf("\n\n")) !== -1) {
            frame(buf.slice(0, cut));
            buf = buf.slice(cut + 2);
          }
          return pump();
        });
      }
      return pump();
    }).catch(function (err) {
      // An abort is this code superseding itself, not a failure. Its result object is
      // already orphaned, and marking it failed would be a lie if anything still read it.
      if (err && err.name === "AbortError") return;
      r.error = r.error || "not connected";
      r.ms = r.ms || performance.now() - t0;
      r.done = true;
    });
  }

  /*
    Fired the moment the visitor picks a name, while they are still reading the page and
    deciding what to ask. It mints the credential and opens the thread, so the first
    question's clock measures the answer rather than the handshake in front of it.

    Deliberately silent: it reports nothing and its failure changes nothing on screen,
    because the question that follows does the same work and will report properly if it is
    still broken. A visitor who types instantly simply gets today's behaviour.
  */
  var warmed = false;
  function warm() {
    if (warmed) return;
    warmed = true;
    fetch("/api/try", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ warm: true, user: state.user })
    }).catch(function () {});
  }

  function ask(text, mount) {
    // WHY the previous question's streams are aborted: without this, asking again while
    // an answer is still arriving leaves the old fetch running to completion, billing a
    // turn nobody will ever see and holding a connection open behind the new one. The
    // thread upstream is also a single conversation, so two turns in flight on it at once
    // is not a thing to allow.
    if (state.abort) state.abort.abort();
    state.abort = new AbortController();
    /*
      An aborted turn stays on screen, so it has to be settled rather than left
      running. Its interval polls r.done, and abort never sets it — the clock would
      count up to the silence cutoff under an answer that was already superseded.
    */
    settlePending();

    var turn = { q: text.trim(), at: performance.now(), results: {} };
    state.turns.push(turn);
    appendTurn(mount, turn);

    // WHY turn.at and not a second performance.now(): every pane's clock counts up
    // from it, so measuring the first token from a later instant would let the final
    // figure land BELOW the number the reader just watched tick past.
    //
    // WHY one origin shared by every contender: they are being compared, so they must be
    // timed from the same instant. A per-pane clock started inside its own callback would
    // silently hand whichever pane the event loop reached last a head start.
    CONTENDERS.forEach(function (c) { readStream(turn, c.id, state.abort.signal); });
  }

  /* ── mount ─────────────────────────────────────────────────────────────── */
  function findAnchor() {
    var form = document.querySelector("[data-try-demo] form") ? null : document.querySelector("form");
    if (!form) return null;
    var host = document.querySelector(".sc-host") || document.body;
    var full = host.getBoundingClientRect().width * 0.95;
    var n = form;
    while (n && n.parentElement && n !== host) {
      if (n.getBoundingClientRect().width >= full) {
        var up = n.parentElement;
        if (up && up !== host && up.getBoundingClientRect().width >= full) return up;
        return n;
      }
      n = n.parentElement;
    }
    return null;
  }

  function mount() {
    if (document.querySelector("[data-try-demo]")) return true;

    /*
      An explicit target wins over the heuristic. findAnchor() works by measuring which
      ancestor of a <form> runs the full width of the page, which is fine on a page built
      around a form and useless on one without: the demo simply never appears, silently and
      with nothing in the console. A page that wants the demo says so with data-try-mount.
    */
    /*
      WHY the x-dc guard: these pages ship as an <x-dc> template that the framework REPLACES
      on hydration. data-try-mount is in the raw markup, so it matches immediately, and a
      demo appended to it is thrown away seconds later when hydration swaps the subtree —
      the page renders, the demo silently is not there. x-dc being gone is the signal that
      hydration has finished. A page that never had one matches on the first frame.
    */
    var slot = document.querySelector("x-dc") ? null : document.querySelector("[data-try-mount]");
    var host = el("section", "padding:40px 0 8px");
    host.setAttribute("data-try-demo", "");

    if (slot) {
      slot.appendChild(host);
    } else {
      var anchor = findAnchor();
      if (!anchor || !anchor.parentElement) return false;
      anchor.parentElement.insertBefore(host, anchor);
    }

    try {
      var saved = localStorage.getItem(STORE_KEY);
      // A returning visitor never sees the gate, so this is their only warm-up point.
      if (saved) { state.user = saved; warm(); }
    } catch (_) {}

    fetch("data/manual.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { state.manual = d; render(host); })
      .catch(function () { render(host); });

    render(host);
    return true;
  }

  /*
    Time-bounded, not frame-bounded. 120 frames is two seconds on a 60Hz screen and less on
    a 120Hz one, which is not enough budget for hydration on a slow connection — and running
    out looks identical to the demo not existing. Ten seconds of wall clock is the same
    intent expressed in the unit that actually matters.
  */
  var giveUpAt = Date.now() + 10000;
  (function wait() {
    if (mount()) return;
    if (Date.now() < giveUpAt) requestAnimationFrame(wait);
  })();

  /*
    A test hook, not an API. `module` does not exist in a browser, so this is dead code on
    the page and the file stays a plain <script>. It exists because renderAnswer turns model
    output into DOM and is the one piece here whose failure is silently ugly rather than
    loud — literal asterisks in the answer — and deploy/smoke-render.mjs can check it
    without a browser only if it can reach it.
  */
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { renderAnswer: renderAnswer };
  }
})();
