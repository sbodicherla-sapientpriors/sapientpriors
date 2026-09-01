#!/usr/bin/env python3
"""
Prepare a generated illustration for use on the site.

    python3 build/prepare-illustration.py <source.png> art/under-construction.webp

Two things it fixes, both of which bite silently:

1. A "transparent" PNG exported from an image tool often has the transparency
   *checkerboard baked into the pixels* — alternating light greys around 245
   and 254. There is no alpha channel to tell you; the file is plain RGB. Left
   alone, `mix-blend-mode: multiply` renders that grid as a visible chequered
   panel on the page.

2. The paper is rarely pure white, so it tints the surface underneath.

The background is found by flood-filling inward from the border through light
pixels, rather than by thresholding. Thresholding would also blow out the
illustration's own cream tones, which sit in the same value range; the artwork's
ink outline keeps its interior disconnected from the border, so connectivity
separates them cleanly where brightness cannot.
"""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage

LIGHT = 232          # anything above this is a candidate for background
MAX_EDGE = 900       # these render at ~460px CSS, so 900 covers retina


def prepare(src, dest):
    a = np.asarray(Image.open(src).convert("RGB")).astype(np.float64)
    lum = a @ [0.2126, 0.7152, 0.0722]

    lbl, _ = ndimage.label(lum > LIGHT)
    edge = set(np.unique(np.concatenate([lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]])))
    edge.discard(0)
    bg = np.isin(lbl, list(edge))

    out = a.copy()
    out[bg] = 255.0
    paper = np.percentile(out[~bg].reshape(-1, 3), 99, axis=0)
    out[~bg] = np.clip(out[~bg] / (paper * 0.985) * 255.0, 0, 255)

    im = Image.fromarray(out.astype(np.uint8))
    im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    im.save(dest, "WEBP", quality=82, method=6)

    chk = np.asarray(Image.open(dest).convert("RGB"))[:50, :50]
    print(f"  {dest}  {im.size[0]}x{im.size[1]}  {os.path.getsize(dest)/1024:.1f} KB")
    print(f"  background cleared: {100*bg.mean():.1f}% of pixels")
    print(f"  corner now {chk.min()}–{chk.max()} (255–255 means the checkerboard is gone)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit(__doc__)
    prepare(os.path.expanduser(sys.argv[1]), sys.argv[2])
