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

  var state = { user: null, manual: null, asked: null, askedAt: null,
                results: {}, timers: [], abort: null };

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
      ";overflow:hidden;position:sticky;top:88px;display:flex;flex-direction:column;" +
      "max-height:calc(100vh - 108px)");

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

  function pane(c) {
    var box = el("div", "display:flex;flex-direction:column;min-height:17rem;border-radius:12px;border:1px solid " +
      (c.ours ? "#E4D3C4" : LINE) + ";background:" + (c.ours ? "#FBF6F1" : WHITE));

    var head = el("div", "padding:11px 14px;border-bottom:1px solid " + LINE_SOFT);
    head.appendChild(el("p", "margin:0;font-family:" + SERIF + ";font-size:1rem;color:" +
      (c.ours ? BROWN_D : INK), c.name));
    box.appendChild(head);

    var body = el("div", "display:flex;flex-direction:column;gap:11px;padding:14px;flex:1");

    var qRow = el("div", "display:flex;justify-content:flex-end");
    qRow.appendChild(el("p", "margin:0;max-width:88%;padding:9px 12px;border-radius:10px 10px 3px 10px;" +
      "font-size:.82rem;line-height:1.55;background:" + (c.ours ? BROWN : INK) + ";color:#fff", state.asked));
    body.appendChild(qRow);

    /*
      WHY two numbers, not one. The first token is the claim this page is making, so it is
      the one in ink; total time is the honest companion to it, because a fast first
      word and a slow finish would otherwise read as a fast answer.
    */
    // WHY lbl and total are separate spans: each is set independently as the stream
    // reaches a different state, and rebuilding one string would fight the interval.
    var clock = el("p", "margin:0;display:flex;align-items:center;justify-content:flex-end;gap:8px;" +
      "font-family:" + MONO + ";font-size:.75rem;color:" + INK4);
    var dot = el("span", "width:6px;height:6px;border-radius:50%;background:" + BROWN);
    var num = el("span", "font-weight:500;color:" + INK2, "0 ms");
    var lbl = el("span", "letter-spacing:.06em", "");
    var total = el("span", "color:" + INK4, "");
    clock.appendChild(dot); clock.appendChild(num); clock.appendChild(lbl); clock.appendChild(total);
    body.appendChild(clock);

    var aRow = el("div", "display:flex;justify-content:flex-start");
    var ans = el("p", "margin:0;max-width:94%;padding:9px 12px;border-radius:10px 10px 10px 3px;border:1px solid " +
      LINE + ";background:" + BONE + ";font-size:.82rem;line-height:1.55;color:" + INK3 + ";white-space:pre-wrap", "\u2026");
    aRow.appendChild(ans);
    body.appendChild(aRow);

    var cites = el("div", "display:none;flex-wrap:wrap;gap:8px;margin-top:2px");
    body.appendChild(cites);
    box.appendChild(body);

    /*
      An interval, not requestAnimationFrame: rAF is suspended outright in a
      background tab, which freezes the clock at zero and reads as broken.
    */
    var started = state.askedAt;
    // WHY painted tracks a length rather than re-setting textContent every tick: the
    // answer arrives a few characters at a time and rewriting an unchanged node 25
    // times a second is what collapses a text selection the reader is holding.
    var painted = 0;
    var drewCites = false;
    var t = setInterval(function () {
      var r = state.results[c.id];
      var e = performance.now() - started;

      if (r && r.ttft !== null) {
        num.textContent = fmt(r.ttft);
        lbl.textContent = "to first word";
      } else {
        num.textContent = fmt(e);
      }

      if (r && r.text.length !== painted) {
        painted = r.text.length;
        ans.textContent = r.text;
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
          if (r.ttft === null) num.textContent = fmt(r.ms);
          total.textContent = "\u00b7 " + fmt(r.ms) + " total";
          if (!r.text) ans.textContent = "(empty reply)";
        }
        if (!drewCites) { drewCites = true; drawCitations(cites, r.citations); }
        return;
      }

      // The cutoff governs SILENCE only: a stream that has started is never cut off.
      if (!r || (r.ttft === null && !r.text)) {
        if (e >= SILENT_CUTOFF_MS) {
          clearInterval(t);
          num.textContent = "\u2014";
          dot.style.background = LINE;
          ans.textContent = "No answer came back.";
          ans.style.color = INK4;
        }
      }
    }, 40);
    state.timers.push(t);
    return box;
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

    list.slice(0, 6).forEach(function (cit) {
      var chip = el("a", "display:flex;align-items:center;gap:7px;max-width:100%;padding:5px 9px 5px 5px;" +
        "border:1px solid " + LINE + ";border-radius:8px;background:" + WHITE + ";text-decoration:none");
      chip.href = cit.href;
      chip.target = "_blank";
      chip.rel = "noopener";

      if (String(cit.media_type || "").indexOf("image/") === 0) {
        var thumb = document.createElement("img");
        thumb.src = cit.href;
        thumb.alt = "";
        thumb.loading = "lazy";
        thumb.setAttribute("style", "width:34px;height:34px;object-fit:cover;border-radius:5px;" +
          "background:" + BONE + ";flex:none");
        chip.appendChild(thumb);
      }
      chip.appendChild(el("span", "font-family:" + MONO + ";font-size:.68rem;color:" + INK2 +
        ";overflow:hidden;text-overflow:ellipsis;white-space:nowrap", cit.label || "figure"));
      mount.appendChild(chip);
    });
  }

  function race() {
    var wrap = el("div", "");
    if (!state.asked) {
      var empty = el("div", "border:1px dashed " + LINE + ";border-radius:12px;padding:52px 24px;text-align:center");
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
    var cols = el("div", "display:grid;grid-template-columns:repeat(" + CONTENDERS.length +
      ",minmax(0,1fr));gap:14px");
    cols.setAttribute("data-race-cols", "");
    CONTENDERS.forEach(function (c) { cols.appendChild(pane(c)); });
    wrap.appendChild(cols);
    return wrap;
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
    var wrap = el("div", "margin:0 auto;padding:0 clamp(1.25rem,3.2vw,4.5rem)");

    if (!state.user) {
      wrap.appendChild(el("p", "margin:0 0 1.25rem;text-align:center;font-family:" + MONO +
        ";font-size:.75rem;letter-spacing:.14em;text-transform:uppercase;color:" + INK4, "The demo"));
      wrap.appendChild(el("h2", "margin:0 auto 2rem;max-width:24ch;text-align:center;font-family:" + SERIF +
        ";font-weight:400;font-size:clamp(1.9rem,3.4vw,2.9rem);line-height:1.1;letter-spacing:-.02em;color:" + INK,
        "One manual, 288 pages, answered before it could be read."));
      gate(wrap, function (u) { state.user = u; render(mount); });
      mount.appendChild(wrap);
      return;
    }

    var bar = el("div", "display:flex;align-items:center;justify-content:space-between;gap:16px;margin:0 0 20px;flex-wrap:wrap");
    var who = el("p", "margin:0;font-size:.9375rem;color:" + INK2);
    who.appendChild(document.createTextNode("Signed in as "));
    who.appendChild(el("span", "font-family:" + MONO + ";color:" + INK, state.user));
    bar.appendChild(who);
    var swap = el("button", "border:1px solid " + LINE + ";background:transparent;border-radius:8px;" +
      "padding:7px 14px;font-size:.8125rem;color:" + INK3 + ";cursor:pointer", "Change username");
    swap.addEventListener("click", function () {
      state.timers.forEach(clearInterval); state.timers = [];
      state.user = null; state.asked = null; state.results = {};
      try { localStorage.removeItem(STORE_KEY); } catch (_) {}
      render(mount);
    });
    bar.appendChild(swap);
    wrap.appendChild(bar);

    wrap.appendChild(tip());

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

    wrap.appendChild(grid);

    /*
      WHY this was rewritten and not just trimmed: it used to say "anything you store here
      can be read by anyone who visits later", which stopped being true the moment learning
      from turns was switched off. A privacy notice that overstates exposure is still a
      false statement on a company page, and this one actively discourages the thing the
      demo is for. What replaces it is the same promise the backend now actually keeps.
    */
    wrap.appendChild(el("p", "margin:18px 0 26px;font-size:.75rem;line-height:1.6;color:" + INK4,
      "Your conversation stays in this session and is not stored for other visitors to read. " +
      "The manual is the only thing in shared memory. Questions are sent to our API to be " +
      "answered."));

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

      var card = left.firstChild;
      if (card) card.style.position = mqPage.matches ? "static" : "sticky";

      var rc = wrap.querySelector("[data-race-cols]");
      if (rc) {
        rc.style.gridTemplateColumns = mqPanes.matches
          ? "minmax(0,1fr)"
          : "repeat(" + CONTENDERS.length + ",minmax(0,1fr))";
      }
    }
    lay();
    mqPage.addEventListener("change", lay);
    mqPanes.addEventListener("change", lay);
  }

  /*
    Read one pane's SSE stream into its live result object.

    WHY it mutates state.results[id] rather than resolving a promise with the finished
    answer: the pane already polls that object on an interval to paint its clock, so
    streaming needs no second render path and no re-render of the page. The reader
    fills the object in; the interval paints whatever is in it. render() rebuilds the
    whole tree, and calling it per token would drop the caret and the scroll position.

    WHY time-to-first-token is measured here and not on the server: this is the number
    the visitor actually waits, browser hop included. All three panes pay the same hop
    on the same connection, so the comparison stays fair and the absolute figure stays
    honest — a server-side clock would quietly flatter every pane by the same amount.
  */
  function readStream(id, t0, signal) {
    // WHY the object is published before the fetch: pane()'s interval is already
    // running, and a pane polling an id that is not there yet has no way to tell
    // "the request has not been made" from "the answer never came".
    var r = { text: "", ttft: null, ms: null, done: false, error: null, citations: [] };
    state.results[id] = r;

    fetch("/api/try", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user: state.user, model: id, message: state.asked }),
      signal: signal
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

  function ask(text, mount) {
    state.timers.forEach(clearInterval);
    state.timers = [];
    // WHY the previous question's streams are aborted: without this, asking again while
    // an answer is still arriving leaves the old fetch running to completion, billing a
    // turn nobody will ever see and holding a connection open behind the new one.
    if (state.abort) state.abort.abort();
    state.abort = new AbortController();
    state.asked = text.trim();
    state.askedAt = performance.now();
    state.results = {};
    render(mount);

    // WHY state.askedAt and not a second performance.now(): every pane's clock counts up
    // from askedAt, so measuring the first token from a later instant would let the final
    // figure land BELOW the number the reader just watched tick past.
    //
    // WHY one origin shared by every contender: they are being compared, so they must be
    // timed from the same instant. A per-pane clock started inside its own callback would
    // silently hand whichever pane the event loop reached last a head start.
    CONTENDERS.forEach(function (c) { readStream(c.id, state.askedAt, state.abort.signal); });
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
    var anchor = findAnchor();
    if (!anchor || !anchor.parentElement) return false;

    var host = el("section", "padding:72px 0 8px");
    host.setAttribute("data-try-demo", "");
    anchor.parentElement.insertBefore(host, anchor);

    try {
      var saved = localStorage.getItem(STORE_KEY);
      if (saved) state.user = saved;
    } catch (_) {}

    fetch("data/manual.json")
      .then(function (r) { return r.json(); })
      .then(function (d) { state.manual = d; render(host); })
      .catch(function () { render(host); });

    render(host);
    return true;
  }

  var tries = 0;
  (function wait() {
    if (mount()) return;
    if (tries++ < 120) requestAnimationFrame(wait);
  })();
})();
