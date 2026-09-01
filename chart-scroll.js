/**
 * Pin the benchmark charts and draw them as you scroll.
 *
 * The section holds still while the two charts reveal along the timeline -
 * accuracy first, then cost - and releases once both are complete.
 *
 * Driven from scroll position rather than CSS scroll-driven animation. The
 * previous attempt animated a <rect> inside a <clipPath>, which lives in
 * <defs> and is never laid out, so `animation-timeline: view()` had no box to
 * measure and the timeline never advanced. Nothing moved, and nothing errored.
 *
 * Fails open: the markup ships fully drawn, this only ever subtracts. If the
 * script does not run, or the browser has no matchMedia, or the reader prefers
 * reduced motion, the charts are simply there - which is the state that matters.
 */
(function () {
  "use strict";

  var SPAN = 260;   // vh of scroll the whole sequence occupies
  var HOLD = 0.08;  // fraction held at each end before and after drawing

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

  function setup() {
    var pin = document.querySelector("[data-chart-pin]");
    if (!pin || pin.dataset.chartPinned) return !!pin;

    var sticky = pin.querySelector("[data-chart-sticky]");
    var rects = [].slice.call(pin.querySelectorAll("[data-wipe]"));
    var labels = [].slice.call(pin.querySelectorAll("[data-chart-label]"));
    if (!sticky || rects.length !== 2) return false;

    var reduced = window.matchMedia
      && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) { pin.dataset.chartPinned = "1"; return true; }

    pin.dataset.chartPinned = "1";

    /*
      Pinning only works if the pinned content fits on screen. Two stacked
      chart cards run to roughly 800px; on a short window that is taller than
      the viewport, and a sticky element taller than its container does not
      stick - it scrolls, and the section reads as broken rather than held.
      Below the fit threshold the charts are simply left drawn.
    */
    var TOP = 88;
    function fits() { return sticky.offsetHeight <= window.innerHeight - TOP - 16; }

    function applyPin() {
      if (fits()) {
        pin.style.height = SPAN + "vh";
        sticky.style.position = "sticky";
        sticky.style.top = TOP + "px";
      } else {
        pin.style.height = "";
        sticky.style.position = "";
        sticky.style.top = "";
        rects.forEach(function (r) { r.setAttribute("width", "800"); });
        labels.forEach(function (l) { l.style.opacity = "1"; });
      }
    }

    // Each label's own x, so it appears exactly when the wipe passes it.
    labels.forEach(function (l) {
      var pct = parseFloat(l.style.left);
      l.dataset.at = isNaN(pct) ? 0 : pct / 100;
      l.style.transition = "opacity 180ms linear";
    });

    function paint() {
      if (!fits()) return;
      var box = pin.getBoundingClientRect();
      var travel = box.height - window.innerHeight;
      if (travel <= 0) return;
      var p = clamp((-box.top) / travel);

      // remap so the charts sit finished for a moment at each end
      var t = clamp((p - HOLD) / (1 - HOLD * 2));

      // accuracy draws over the first half, cost over the second
      var acc = clamp(t / 0.5);
      var cost = clamp((t - 0.5) / 0.5);

      rects[0].setAttribute("width", (800 * acc).toFixed(1));
      rects[1].setAttribute("width", (800 * cost).toFixed(1));

      labels.forEach(function (l, i) {
        var chart = l.closest("[data-chart-card]");
        var prog = chart && chart.dataset.chart === "cost" ? cost : acc;
        l.style.opacity = prog >= l.dataset.at - 0.005 ? "1" : "0";
      });
    }

    var queued = false;
    function onScroll() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; paint(); });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", function () { applyPin(); onScroll(); },
                            { passive: true });
    applyPin();
    paint();
    return true;
  }

  // The runtime renders after this deferred script, and re-renders on state
  // changes, so watch rather than wait once.
  setup();
  var obs = new MutationObserver(function () { setup(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
