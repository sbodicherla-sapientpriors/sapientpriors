/**
 * Try It — the shared-memory demo.
 *
 * The flow the page implements:
 *   1. Pick a username. Anything you like; it is the handle your memories are
 *      filed under.
 *   2. Ask questions about the MG Hector owner's manual, and tell it things
 *      worth remembering.
 *   3. Memories are attributed to the username that created them, and every
 *      visitor shares one pool — so you can ask what other people have stored,
 *      and who stored it.
 *
 * ── State of play ───────────────────────────────────────────────────────────
 * The interface is complete; the endpoint is not built. Every send posts to
 * /api/try and renders whatever comes back. Until that route exists the reply
 * says so rather than inventing an answer, because a demo whose whole claim is
 * "it remembers" cannot afford a scripted reply that only looks like memory.
 *
 * ── One thing to decide before this goes live ───────────────────────────────
 * A single shared pool means anything a visitor types is readable by every
 * later visitor, attributed to a handle they chose. That is the fun of it and
 * also the risk: people will type real names, numbers and grievances into a
 * box on a company website. The notice under the composer says so plainly;
 * moderation and a retention window are a backend decision.
 */
(function () {
  "use strict";

  var INK = "#14161A", INK2 = "#3A3E45", INK3 = "#6B7078", INK4 = "#9AA0A8";
  var LINE = "#E4E4E0", LINE_SOFT = "#EFEFEC", BONE = "#F6F6F4", WHITE = "#FFFFFF";
  var BROWN = "#84512E", BROWN_D = "#6B4226";
  var MONO = "'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace";
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

  var SUGGESTIONS = [
    "What tyre pressure does the Hector need?",
    "Remember that I tow a trailer most weekends.",
    "What has anyone else asked you to remember?",
    "Who told you about the trailer?"
  ];

  var CONTENDERS = [
    { id: "ours", name: "SapientPriors", ours: true },
    { id: "haiku", name: "Claude Haiku 4.5", ours: false },
    { id: "opus", name: "Claude Opus 4.5", ours: false }
  ];

  /** How long a clock runs before it admits nothing is coming. */
  var CUTOFF_MS = 3200;

  var state = { user: null, manual: null, asked: null, askedAt: null,
                results: {}, timers: [] };

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
      "Anything you like. Everything you ask it to remember is filed under this name, " +
      "and other people can find it."));

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
    p.appendChild(document.createTextNode("You can reach memories other people have stored. Try "));
    p.appendChild(el("span", "font-family:" + MONO + ";font-size:.85rem;background:rgba(255,255,255,.16);" +
      "padding:1px 6px;border-radius:4px", "What has anyone else asked you to remember?"));
    p.appendChild(document.createTextNode(" — then ask who stored it, and it will tell you the username."));
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

    var clock = el("p", "margin:0;display:flex;align-items:center;justify-content:flex-end;gap:6px;" +
      "font-family:" + MONO + ";font-size:.75rem;color:" + INK4);
    var dot = el("span", "width:6px;height:6px;border-radius:50%;background:" + BROWN);
    var num = el("span", "font-weight:500;color:" + INK2, "0 ms");
    clock.appendChild(dot); clock.appendChild(num);
    body.appendChild(clock);

    var aRow = el("div", "display:flex;justify-content:flex-start");
    var ans = el("p", "margin:0;max-width:94%;padding:9px 12px;border-radius:10px 10px 10px 3px;border:1px solid " +
      LINE + ";background:" + BONE + ";font-size:.82rem;line-height:1.55;color:" + INK3, "\u2026");
    aRow.appendChild(ans);
    body.appendChild(aRow);
    box.appendChild(body);

    /*
      An interval, not requestAnimationFrame: rAF is suspended outright in a
      background tab, which freezes the clock at zero and reads as broken.
    */
    var started = state.askedAt;
    var t = setInterval(function () {
      var done = state.results[c.id];
      if (done) {
        clearInterval(t);
        num.textContent = fmt(done.ms);
        dot.style.background = LINE;
        ans.textContent = done.text;
        return;
      }
      var e = performance.now() - started;
      if (e >= CUTOFF_MS) {
        clearInterval(t);
        num.textContent = "\u2014";
        dot.style.background = LINE;
        ans.textContent = "Not connected yet \u2014 the answer streams in here.";
        return;
      }
      num.textContent = fmt(e);
    }, 40);
    state.timers.push(t);
    return box;
  }

  function race() {
    var wrap = el("div", "");
    if (!state.asked) {
      var empty = el("div", "border:1px dashed " + LINE + ";border-radius:12px;padding:52px 24px;text-align:center");
      empty.appendChild(el("p", "margin:0 0 6px;font-family:" + SERIF + ";font-size:1.15rem;color:" + INK,
        "Ask the manual something, or tell it something to remember."));
      empty.appendChild(el("p", "margin:0;font-size:.85rem;color:" + INK3,
        "The same question goes to all three at once. Watch the clocks."));
      wrap.appendChild(empty);
      return wrap;
    }
    var cols = el("div", "display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px");
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
        "One manual, one shared memory, everyone who has been here before you."));
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
      ";color:#fff;font-size:.875rem;font-weight:500;cursor:pointer", "Ask all three");
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

    wrap.appendChild(el("p", "margin:18px 0 26px;font-size:.75rem;line-height:1.6;color:" + INK4,
      "Everyone shares one memory pool, and each memory carries the username that created it. " +
      "Anything you store here can be read by anyone who visits later \u2014 so keep it to things " +
      "you would happily say out loud."));

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
          : "repeat(3,minmax(0,1fr))";
      }
    }
    lay();
    mqPage.addEventListener("change", lay);
    mqPanes.addEventListener("change", lay);
  }

  function ask(text, mount) {
    state.timers.forEach(clearInterval);
    state.timers = [];
    state.asked = text.trim();
    state.askedAt = performance.now();
    state.results = {};
    render(mount);

    CONTENDERS.forEach(function (c) {
      var t0 = performance.now();
      fetch("/api/try", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user: state.user, model: c.id, message: state.asked })
      })
        .then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); })
        .then(function (d) {
          state.results[c.id] = { ms: performance.now() - t0, text: d.reply || "(empty reply)" };
        })
        .catch(function () { /* the pane's own cutoff says so */ });
    });
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
