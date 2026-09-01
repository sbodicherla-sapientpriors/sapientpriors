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

  /*
    Each chart is driven by its own box, not by one progress value shared
    across the section. Sharing meant the cost chart's completion was tied to
    how far the whole section had travelled, so it finished after it had
    already scrolled past the top of the screen - you never saw the end of the
    line you were being asked to read.

    Per chart: the draw starts as the card enters from the bottom and finishes
    once the card is fully on screen with a little room to spare. So each chart
    is complete exactly when you can see all of it, and the accuracy chart is
    done by the time the cost chart arrives.
  */
  var TAIL = 70;   // px of extra scroll past "fully visible" before completion

  function clamp(v) { return v < 0 ? 0 : v > 1 ? 1 : v; }

  function setup() {
    var pin = document.querySelector("[data-chart-pin]");
    if (!pin || pin.dataset.chartOn) return !!pin;

    var cards = [].slice.call(pin.querySelectorAll("[data-chart-card]"));
    var rects = cards.map(function (c) { return c.querySelector("[data-wipe]"); });
    var labels = [].slice.call(pin.querySelectorAll("[data-chart-label]"));
    if (cards.length !== 2 || rects.some(function (r) { return !r; })) return false;
    pin.dataset.chartOn = "1";

    labels.forEach(function (l) {
      var pct = parseFloat(l.style.left);
      l.dataset.at = isNaN(pct) ? 0 : pct / 100;
      l.style.transition = "opacity 150ms linear";
      l._card = l.closest("[data-chart-card]");
    });

    function drawn(card) {
      var box = card.getBoundingClientRect();
      var vh = window.innerHeight;
      var span = box.height + TAIL;
      if (span <= 0) return 1;
      return clamp((vh - box.top) / span);
    }

    function paint() {
      cards.forEach(function (card, i) {
        var p = drawn(card);
        if (rects[i]) rects[i].setAttribute("width", (800 * p).toFixed(1));
        card._p = p;
      });
      labels.forEach(function (l) {
        var card = l._card;
        var p = card ? card._p || 0 : 0;
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
    window.addEventListener("resize", onScroll, { passive: true });
    paint();
    setTimeout(paint, 400);   // heights settle after the runtime finishes
    return true;
  }

  setup();
  var obs = new MutationObserver(function () { setup(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
