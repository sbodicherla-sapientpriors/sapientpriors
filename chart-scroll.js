/**
 * Draw the benchmark charts as they scroll.
 *
 * Two modes, and it always animates:
 *
 *   pinned      when the two cards fit on screen, the section holds still
 *               while they draw, then releases.
 *   scroll-past when they do not fit - which is most laptops, since two
 *               stacked cards run to roughly 700-800px - the charts draw as
 *               the section travels through the viewport instead.
 *
 * The first version pinned or did nothing, and "does not fit" is the common
 * case, so on most screens it did nothing. A sticky element taller than the
 * viewport does not stick, so pinning genuinely cannot be forced here; the
 * animation just must not depend on it.
 *
 * Fails open: the markup ships fully drawn and this only ever subtracts. No
 * script, or reduced motion, and the charts are simply complete.
 */
(function () {
  "use strict";

  var TOP = 88;      // sticky offset, clears the fixed nav
  var SPAN = 240;    // vh of scroll the pinned sequence occupies
  var HOLD = 0.08;   // fraction held finished at each end

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

  function setup() {
    var pin = document.querySelector("[data-chart-pin]");
    if (!pin || pin.dataset.chartOn) return !!pin;

    var sticky = pin.querySelector("[data-chart-sticky]");
    var rects = [].slice.call(pin.querySelectorAll("[data-wipe]"));
    var labels = [].slice.call(pin.querySelectorAll("[data-chart-label]"));
    if (!sticky || rects.length !== 2) return false;

    if (window.matchMedia
        && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      pin.dataset.chartOn = "reduced";
      return true;
    }
    pin.dataset.chartOn = "1";

    labels.forEach(function (l) {
      var pct = parseFloat(l.style.left);
      l.dataset.at = isNaN(pct) ? 0 : pct / 100;
      l.style.transition = "opacity 160ms linear";
      var card = l.closest("[data-chart-card]");
      l.dataset.series = card && card.dataset.chart === "cost" ? "cost" : "acc";
    });

    var pinned = false;

    function layout() {
      pinned = sticky.offsetHeight <= window.innerHeight - TOP - 16;
      pin.style.height = pinned ? SPAN + "vh" : "";
      sticky.style.position = pinned ? "sticky" : "";
      sticky.style.top = pinned ? TOP + "px" : "";
      pin.dataset.chartMode = pinned ? "pinned" : "scroll-past";
    }

    function progress() {
      var box = pin.getBoundingClientRect();
      var vh = window.innerHeight;
      if (pinned) {
        var travel = box.height - vh;
        if (travel <= 0) return 1;
        return clamp(-box.top / travel);
      }
      // Not pinned: run from the moment the section is well into view to
      // shortly before it leaves, so the draw finishes while it is readable.
      var from = vh * 0.85;
      var to = vh * 0.30 - box.height;
      if (from - to <= 0) return 1;
      return clamp((from - box.top) / (from - to));
    }

    function paint() {
      var t = clamp((progress() - HOLD) / (1 - HOLD * 2));
      var acc = clamp(t / 0.5);
      var cost = clamp((t - 0.5) / 0.5);
      rects[0].setAttribute("width", (800 * acc).toFixed(1));
      rects[1].setAttribute("width", (800 * cost).toFixed(1));
      labels.forEach(function (l) {
        var p = l.dataset.series === "cost" ? cost : acc;
        l.style.opacity = p >= (+l.dataset.at) - 0.004 ? "1" : "0";
      });
    }

    var queued = false;
    function onScroll() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; paint(); });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () { layout(); paint(); },
                            { passive: true });

    layout();
    paint();
    // The runtime finishes rendering after this runs, which changes heights.
    setTimeout(function () { layout(); paint(); }, 400);
    return true;
  }

  setup();
  var obs = new MutationObserver(function () { setup(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
