# -*- coding: utf-8 -*-
"""
Inject the scroll-motion module into every page.

Kept as its own patch module rather than folded into patch_ui so it can be
dropped by deleting one line from build.py - this is on trial, and a trial you
cannot reverse in one move is not a trial.
"""
import glob
import io
import os

TAG = '<script src="scroll-motion.js" defer></script>'

# A corner panel for judging the layers separately. Sandbox only: apply() takes
# `panel` and the production build would pass False.
PANEL = """
<div id="sp-motion-panel" style="position:fixed;left:16px;bottom:16px;z-index:99999;
background:rgba(255,255,255,.94);border:1px solid #CFCFC9;border-radius:10px;
padding:10px 12px;font:12px/1.5 ui-monospace,Menlo,monospace;color:#14161A;
box-shadow:0 2px 14px rgba(0,0,0,.08);backdrop-filter:blur(6px)">
<div style="font-weight:600;letter-spacing:.08em;text-transform:uppercase;
font-size:10px;color:#6B7078;margin-bottom:6px">Scroll motion</div>
<label style="display:block;cursor:pointer"><input type="checkbox" data-mo="lines"> line reveal</label>
<label style="display:block;cursor:pointer"><input type="checkbox" data-mo="stagger"> rise + stagger</label>
<label style="display:block;cursor:pointer"><input type="checkbox" data-mo="parallax"> parallax</label>
<label style="display:block;cursor:pointer"><input type="checkbox" data-mo="smooth"> smooth scroll</label>
<div style="margin-top:6px;font-size:10px;color:#9AA0A8">reloads on change</div>
</div>
<script>
(function(){
  function sync(){
    var f = (window.__spMotion && window.__spMotion.flags) || {};
    document.querySelectorAll('#sp-motion-panel input').forEach(function(i){
      i.checked = !!f[i.dataset.mo];
      i.onchange = function(){ window.__spMotion.set(i.dataset.mo, i.checked); };
    });
  }
  if (document.readyState === 'loading')
    document.addEventListener('DOMContentLoaded', function(){ setTimeout(sync, 80); });
  else setTimeout(sync, 80);
})();
</script>
"""


def apply(out, panel=False):
    n = 0
    for path in sorted(glob.glob(os.path.join(out, "*.html"))):
        s = io.open(path, encoding="utf-8", errors="surrogateescape").read()
        if TAG in s:
            continue
        add = TAG + (PANEL if panel else "")
        if "</body>" in s:
            s = s.replace("</body>", add + "\n</body>", 1)
        else:
            s = s + add
        io.open(path, "w", encoding="utf-8", errors="surrogateescape").write(s)
        n += 1
    print("  motion injected into %d pages%s" % (n, " (with panel)" if panel else ""))
    if n == 0:
        print("  no pages took the motion script - CHECK")
