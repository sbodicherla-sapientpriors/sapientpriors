/**
 * Scroll motion, modelled on the reference site's system.
 *
 * The design file that came with the reference carries no motion at all - it is
 * tokens, type and components - so the behaviour here was read off the running
 * site instead. What that site does, stripped of its markup:
 *
 *   1. split-text   headings are cut into lines, each line sitting inside an
 *                   overflow-clipped parent and starting translated fully below
 *                   it, so it wipes up into place rather than fading. Lines are
 *                   staggered 0.08s apart, 1.2s each, easeOutQuart.
 *   2. parallax     marked elements drift against the scroll at a ratio of
 *                   their distance from the viewport centre.
 *   3. appear       a class toggled by an observer drives every transition; no
 *                   animation library anywhere on that site either.
 *
 * The measured constants are kept exactly: 1.2s, cubic-bezier(.165,.84,.44,1),
 * 0.08s per line. The parallax formula was derived from their running site by
 * sampling one element across seven scroll positions - translate is
 * ratio x (centre - untranslated top), which is why an element sits still when
 * it is centred and drifts hardest at the edges.
 *
 * Two deliberate departures:
 *
 *   - Reveals replay. The reference plays each heading once and leaves it.
 *     This site's existing reveals were explicitly changed to re-run when you
 *     scroll back up, and one system that forgets while another repeats reads
 *     as a bug, so these repeat too.
 *   - No prefers-reduced-motion gate, matching the decision already taken for
 *     the chart animation on this site.
 *
 * Nothing here is imported from the reference: no colour, type, spacing or
 * markup. Only the mechanics.
 */
(function () {
  "use strict";

  var EASE  = "cubic-bezier(.165,.84,.44,1)";  /* easeOutQuart, as measured */
  var DUR   = 1.2;    /* seconds per line */
  var STEP  = 0.08;   /* stagger between lines */
  var LEAD  = 0.04;   /* delay before the first line */

  /* Toggles, so each layer can be judged on its own: ?motion=lines,parallax
     turns everything else off; ?motion=off disables the lot. */
  /* parallax is built and correct but stays off: this site has one photograph,
     and a single drifting image among logos reads as a fault rather than depth.
     Turn it on with ?motion=lines,stagger,smooth,parallax the day that changes. */
  var on = { lines: true, parallax: false, stagger: true, smooth: true };
  (function readFlags() {
    var q = new URLSearchParams(location.search);
    var m = q.get("motion");
    if (m !== null) {
      var want = m.split(",").map(function (s) { return s.trim(); });
      Object.keys(on).forEach(function (k) { on[k] = want.indexOf(k) !== -1; });
    }
    if (q.get("smooth") !== null) on.smooth = q.get("smooth") !== "0";
    try {
      var saved = localStorage.getItem("sp-motion");
      if (saved && m === null) on = Object.assign(on, JSON.parse(saved));
    } catch (e) {}
  })();

  /* ---------------------------------------------------------------- styles */

  var css = document.createElement("style");
  css.textContent = [
    /* A line's parent clips it; the line starts below that clip. overflow:clip
       rather than hidden so this never becomes a scroll container - a clipped
       heading that can be scrolled sideways by a trackpad is a real bug.
       The padding/margin pair keeps descenders (g, y, p) off the clip edge. */
    ".sp-lp{overflow:hidden;overflow:clip;display:block}",
    ".sp-line{display:block;transform:translateY(112%);will-change:transform;",
    "transform-origin:left bottom;padding-bottom:.14em;margin-bottom:-.14em}",
    ".is-appear .sp-line{transform:translateY(0)}",

    /* Blocks that cannot be split - anything the page's own runtime owns and
       rewrites - get the same entrance without the restructuring. */
    ".sp-rise{opacity:0;transform:translateY(22px);will-change:transform,opacity}",
    ".is-appear.sp-rise,.is-appear .sp-rise{opacity:1;transform:translateY(0)}",

    ".sp-para{will-change:transform}"
  ].join("");
  document.head.appendChild(css);

  /* ------------------------------------------------------------ splitting */

  /* Runtime-owned nodes. The page is a Claude Design export whose runtime
     re-renders and REPLACES nodes after hydration; anything carrying an
     interpolation or a counter binding will be rewritten under us, so those
     are never restructured - they take the .sp-rise path instead. */
  function ownedByRuntime(el) {
    return !!el.querySelector(".sc-interp,[data-count],[data-to]");
  }

  function words(el) {
    var out = [];
    (function walk(node, style) {
      for (var i = 0; i < node.childNodes.length; i++) {
        var n = node.childNodes[i];
        if (n.nodeType === 3) {
          n.nodeValue.split(/\s+/).forEach(function (w) {
            if (w) out.push({ text: w, style: style });
          });
        } else if (n.nodeType === 1) {
          walk(n, n.getAttribute("style") || style);
        }
      }
    })(el, "");
    return out;
  }

  function split(el) {
    if (el.dataset.spSplit === "1" || ownedByRuntime(el)) return false;
    var ws = words(el);
    if (!ws.length) return false;

    if (el.__spHTML == null) el__store(el);

    /* Pass one: lay the words out inline and measure which line each landed on.
       textContent, never innerHTML - a heading containing & or < would other-
       wise be re-parsed as markup. */
    var frag = document.createDocumentFragment();
    var spans = ws.map(function (o, i) {
      var s = document.createElement("span");
      s.textContent = o.text;
      if (o.style) s.setAttribute("style", o.style);
      frag.appendChild(s);
      if (i < ws.length - 1) frag.appendChild(document.createTextNode(" "));
      return s;
    });
    el.textContent = "";
    el.appendChild(frag);

    var lines = [], last = null;
    spans.forEach(function (s) {
      var t = s.offsetTop;
      if (last === null || Math.abs(t - last) > 3) { lines.push([]); last = t; }
      lines[lines.length - 1].push(s);
    });

    /* Pass two: rebuild as one clipped parent per line. */
    var out = document.createDocumentFragment();
    lines.forEach(function (group, i) {
      var lp = document.createElement("div");
      lp.className = "sp-lp";
      var ln = document.createElement("div");
      ln.className = "sp-line";
      ln.style.transition = "transform " + DUR + "s " + EASE + " " +
                            (LEAD + i * STEP).toFixed(2) + "s";
      group.forEach(function (s, j) {
        if (j) ln.appendChild(document.createTextNode(" "));
        ln.appendChild(s);
      });
      lp.appendChild(ln);
      out.appendChild(lp);
    });
    el.textContent = "";
    el.appendChild(out);
    el.dataset.spSplit = "1";
    return true;
  }

  function el__store(el) { el.__spHTML = el.innerHTML; }

  /* Re-splitting on resize: the line breaks change with the column width, so a
     heading split at 1440px is wrong at 900px. Restore, then split again. */
  function resplit(el) {
    if (el.__spHTML == null) return;
    el.innerHTML = el.__spHTML;
    delete el.dataset.spSplit;
    split(el);
  }

  /* --------------------------------------------------------------- targets */

  /* "Is this a section headline?" - asked in ems of the viewport rather than in
     absolute pixels, because the same h2 is 55px wide and 30px narrow, and an
     absolute threshold silently switched the whole effect off on a phone. */
  function big(el) {
    var min = window.innerWidth < 768 ? 22 : 34;
    return parseFloat(getComputedStyle(el).fontSize) >= min;
  }
  function inChrome(el) { return !!el.closest("nav,header,footer,[data-apply-form]"); }

  var split_els = [], rise_els = [], paras = [];

  function collect() {
    split_els = []; rise_els = []; paras = [];

    [].forEach.call(document.querySelectorAll("h1,h2"), function (h) {
      if (inChrome(h) || !big(h)) return;
      (ownedByRuntime(h) ? rise_els : split_els).push(h);
    });

    /* Sub-heads and lead paragraphs rise rather than wipe - a wipe on every
       block of text at every size is the thing that makes a site feel like it
       is performing rather than moving. */
    [].forEach.call(document.querySelectorAll("h3"), function (h) {
      if (inChrome(h)) return;
      if (parseFloat(getComputedStyle(h).fontSize) >= (window.innerWidth < 768 ? 18 : 26))
        rise_els.push(h);
    });

    /* Photographs only - height is the proxy. Logos and marks were picked up by
       an earlier, looser rule and drifting a logo inside a row of logos reads as
       a rendering fault, not as depth.

       An image that exactly fills its frame cannot be moved without exposing an
       edge: at 26px of drift in a 224px band this opened a 26px strip of empty
       background along the top. So the drift is bounded to a fraction of the
       height and the image is scaled by just over twice that fraction, which
       keeps the frame covered at both extremes. */
    [].forEach.call(document.querySelectorAll("img"), function (img) {
      if (inChrome(img)) return;
      /* offsetHeight, not getBoundingClientRect: the rect includes the scale
         this function itself applied, so re-collecting fed its own output back
         in and the drift grew on every pass. offsetHeight is layout only and a
         transform cannot move it. */
      var h = img.offsetHeight;
      if (h < 150) return;
      var max = Math.min(24, h * 0.06);
      paras.push({ el: img, ratio: -0.12, ty: 0, max: max,
                   scale: 1 + (2 * max + 4) / h });
    });
  }

  /* --------------------------------------------------------------- appear */

  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      /* Both directions: leaving re-arms, so scrolling back up replays it. */
      e.target.classList.toggle("is-appear", e.isIntersecting);
    });
  }, { rootMargin: "0px 0px -10% 0px", threshold: 0 });

  function arm() {
    collect();
    if (on.lines) split_els.forEach(function (h) { split(h); io.observe(h); });
    if (on.stagger) rise_els.forEach(function (h) {
      h.classList.add("sp-rise");
      h.style.transition = "opacity .9s " + EASE + ", transform .9s " + EASE;
      io.observe(h);
    });
    if (on.stagger) staggerGrids();
  }

  /* Grid children enter one after another rather than as a block. */
  function staggerGrids() {
    [].forEach.call(document.querySelectorAll("[data-founder-cards]"), function (g) {
      [].forEach.call(g.children, function (c, i) {
        c.classList.add("sp-rise");
        c.style.transition = "opacity .8s " + EASE + " " + (i * 0.09).toFixed(2) +
                             "s, transform .8s " + EASE + " " + (i * 0.09).toFixed(2) + "s";
        io.observe(c);
      });
    });
  }

  /* ------------------------------------------------------------- parallax */

  function paintParallax() {
    var vh = window.innerHeight;
    for (var i = 0; i < paras.length; i++) {
      var o = paras[i], r = o.el.getBoundingClientRect();
      var h = o.el.offsetHeight;                       /* untransformed height */
      var rawTop = r.top + (r.height - h) / 2 - o.ty;  /* undo scale, then drift */
      var d = (vh - h) / 2 - rawTop;                   /* distance from centre */
      var ty = o.ratio * d;
      if (ty > o.max) ty = o.max; else if (ty < -o.max) ty = -o.max;
      o.ty = ty;
      o.el.style.transform = "translate3d(0," + ty.toFixed(2) + "px,0)" +
                             (o.scale !== 1 ? " scale(" + o.scale + ")" : "");
    }
  }

  /* ------------------------------------------------------- in-page anchors */

  /* The nav CTA points at "SapientPriors.dc.html#access". The runtime builds
     that href from the page's own name, and on the home page it does so after
     hydration, so it is not something the build can rewrite there.

     Followed literally it is a navigation to a different document: the page
     reloads, the curtain plays again, and because #access does not exist until
     React has rendered, the browser's own fragment jump finds nothing and
     leaves you at the top. Which is what it looked like from outside - a button
     that reloads the page and goes nowhere.

     So a link whose fragment names something already on this page is treated as
     an in-page jump whatever its path claims. A link to a section that really
     is on another page still navigates. */

  function navOffset() {
    var best = 0;
    [].forEach.call(document.querySelectorAll("div,header,nav"), function (el) {
      var cs = getComputedStyle(el);
      if (cs.position !== "fixed" || cs.visibility === "hidden") return;
      var r = el.getBoundingClientRect();
      if (r.top <= 1 && r.height > 24 && r.height < 140 && r.width > window.innerWidth * 0.6)
        best = Math.max(best, r.height);
    });
    return best ? best + 12 : 84;
  }

  function fragmentTarget(href) {
    var h = (href || "").indexOf("#");
    if (h === -1) return null;
    var id = href.slice(h + 1);
    if (!id) return null;
    try { return document.getElementById(decodeURIComponent(id)); } catch (e) { return null; }
  }

  function goTo(el) {
    var y = el.getBoundingClientRect().top + window.scrollY - navOffset();
    window.scrollTo({ top: Math.max(0, y), behavior: "smooth" });
  }

  document.addEventListener("click", function (e) {
    if (e.defaultPrevented || e.button !== 0) return;
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var a = e.target && e.target.closest && e.target.closest("a[href]");
    if (!a || a.target === "_blank") return;
    var el = fragmentTarget(a.getAttribute("href"));
    if (!el) return;                       /* really is on another page */
    e.preventDefault();
    goTo(el);
    var id = a.getAttribute("href").split("#")[1];
    if (window.history && history.replaceState) {
      try { history.replaceState(null, "", "#" + id); } catch (err) {}
    }
  }, true);

  /* Arriving with a fragment already in the URL - which is what the redirect
     from the old duplicate home page produces - the element does not exist yet
     at load, so the browser's jump has already failed by the time it does. */
  function honourHash() {
    if (!location.hash || location.hash.length < 2) return;
    var el = null;
    try { el = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch (e) {}
    if (el && window.scrollY < 40) goTo(el);
  }

  /* --------------------------------------------------------- smooth scroll */

  /* The reference lerps the page rather than letting it land where the wheel
     put it. Implemented against window.scrollTo rather than by transforming a
     fixed wrapper, because this page has a fixed nav and sticky sections that a
     transformed wrapper would break. Off unless asked for: it overrides trackpad
     momentum, which is a taste question, not an improvement. */
  var smooth = null;
  function initSmooth() {
    if (smooth || !on.smooth) return;
    var target = window.scrollY, running = false;
    function step() {
      var y = window.scrollY;
      var next = y + (target - y) * 0.12;
      if (Math.abs(target - next) < 0.4) { window.scrollTo(0, target); running = false; return; }
      window.scrollTo(0, next);
      requestAnimationFrame(step);
    }
    /* Anything the pointer is over that can still scroll on its own keeps its
       wheel. Without this, taking the page's wheel event would freeze every
       nested scroller on the site - the wide tables and code blocks that scroll
       inside their own box - because preventDefault kills the whole gesture,
       not just the part that would have moved the page. */
    function nestedScroller(node, dy) {
      for (var el = node; el && el.nodeType === 1 && el !== document.body;
           el = el.parentElement) {
        var oy = getComputedStyle(el).overflowY;
        if ((oy === "auto" || oy === "scroll") &&
            el.scrollHeight > el.clientHeight + 1) {
          if (dy < 0 && el.scrollTop > 0) return true;
          if (dy > 0 && el.scrollTop < el.scrollHeight - el.clientHeight - 1) return true;
        }
      }
      return false;
    }

    smooth = function (e) {
      if (e.ctrlKey) return;                      /* pinch-zoom */
      var dy = e.deltaY;
      if (e.deltaMode === 1) dy *= 16;            /* some mice report lines */
      else if (e.deltaMode === 2) dy *= window.innerHeight;
      if (nestedScroller(e.target, dy)) return;
      e.preventDefault();
      var max = document.documentElement.scrollHeight - window.innerHeight;
      target = Math.max(0, Math.min(max, target + dy));
      if (!running) { running = true; requestAnimationFrame(step); }
    };
    window.addEventListener("wheel", smooth, { passive: false });
    window.addEventListener("scroll", function () {
      if (!running) target = window.scrollY;      /* keyboard, anchors, bar */
    }, { passive: true });
  }

  /* ------------------------------------------------------------------ run */

  var raf = 0, lastY = -1;
  function tick() {
    var y = window.scrollY;
    if (y !== lastY) { lastY = y; if (on.parallax) paintParallax(); }
    raf = requestAnimationFrame(tick);
  }

  function boot() {
    arm();
    if (on.parallax) paintParallax();
    if (on.smooth) initSmooth();
    if (!raf) tick();
  }

  /* The runtime replaces nodes after hydration, so this cannot run once on load
     and be done. Observe unconditionally and re-arm when the tree changes -
     the lesson from the curtain wordmark, which mounted correctly and was then
     silently replaced. Debounced, and our own writes are ignored via the
     data-sp-split guard. */
  var settle = 0;
  new MutationObserver(function () {
    clearTimeout(settle);
    settle = setTimeout(boot, 120);
  }).observe(document.body, { childList: true, subtree: true });

  var rz = 0;
  window.addEventListener("resize", function () {
    clearTimeout(rz);
    rz = setTimeout(function () {
      split_els.forEach(resplit);
      boot();
      if (on.parallax) paintParallax();
    }, 180);
  }, { passive: true });

  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", boot);
  else boot();
  /* The curtain holds the page for ~3s; re-arm after it lifts. */
  setTimeout(boot, 3600);
  setTimeout(honourHash, 3800);
  window.addEventListener("hashchange", honourHash);

  window.__spMotion = { flags: on, boot: boot,
    set: function (k, v) {
      on[k] = v;
      try { localStorage.setItem("sp-motion", JSON.stringify(on)); } catch (e) {}
      location.reload();
    } };
})();
