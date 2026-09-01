/**
 * Draw the benchmark charts as the section scrolls through the viewport.
 *
 * No pinning. Pinning was tried and removed: the pinned wrapper has to be
 * taller than the viewport to have anything to scroll through, which meant the
 * section arrived at progress 0 and you scrolled ~770px past empty charts
 * before a line appeared, then scrolled a screen of blank space after they
 * finished. The draw is the point; the holding was not worth either cost.
 *
 * Progress runs from the section being most of the way into view to it being
 * most of the way out, so both charts complete while they are comfortably
 * readable rather than at the edges of the screen.
 *
 * Deliberately not gated on prefers-reduced-motion. Asked for explicitly. It is
 * a scroll-linked reveal - no autoplay, no parallax, no looping, nothing moves
 * unless the reader moves it - which is the mild end of motion, but it is still
 * an accessibility preference being overridden knowingly.
 *
 * Fails open: the markup ships fully drawn and this only ever subtracts.
 */
(function () {
  "use strict";

  var START = 0.92;  // fraction of viewport height at which drawing begins
  var END = 0.22;    // where it finishes, as a fraction of the way out

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

  function setup() {
    var pin = document.querySelector("[data-chart-pin]");
    if (!pin || pin.dataset.chartOn) return !!pin;

    var rects = [].slice.call(pin.querySelectorAll("[data-wipe]"));
    var labels = [].slice.call(pin.querySelectorAll("[data-chart-label]"));
    if (rects.length !== 2) return false;
    pin.dataset.chartOn = "1";

    labels.forEach(function (l) {
      var pct = parseFloat(l.style.left);
      l.dataset.at = isNaN(pct) ? 0 : pct / 100;
      l.style.transition = "opacity 150ms linear";
      var card = l.closest("[data-chart-card]");
      l.dataset.series = card && card.dataset.chart === "cost" ? "cost" : "acc";
    });

    function paint() {
      var box = pin.getBoundingClientRect();
      var vh = window.innerHeight;
      var from = vh * START;
      var to = vh * END - box.height;
      var p = from - to <= 0 ? 1 : clamp((from - box.top) / (from - to));

      // accuracy over the first half, cost over the second
      var acc = clamp(p / 0.5);
      var cost = clamp((p - 0.5) / 0.5);
      rects[0].setAttribute("width", (800 * acc).toFixed(1));
      rects[1].setAttribute("width", (800 * cost).toFixed(1));
      labels.forEach(function (l) {
        var prog = l.dataset.series === "cost" ? cost : acc;
        l.style.opacity = prog >= (+l.dataset.at) - 0.004 ? "1" : "0";
      });
    }

    var queued = false;
    function onScroll() {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () { queued = false; paint(); });
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll, { passive: true });
    paint();
    setTimeout(paint, 400);   // heights settle after the runtime finishes
    return true;
  }

  setup();
  var obs = new MutationObserver(function () { setup(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
