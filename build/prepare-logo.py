#!/usr/bin/env python3
"""
Turn a logo image into a single-ink mask for the alumni strip.

    python3 build/prepare-logo.py <source> <dest.webp> <mode>

The strip paints a box with an ink token and uses the file as a CSS mask, so
only the alpha channel matters — colour in the source is discarded. That is
what lets one asset work on the light page and the inverted band without a
second file.

Modes, because source logos do not agree on polarity:

  dark      dark artwork on a light background (most logos)
  light     light artwork on a dark background — inverted, or the ink would be
            the background and the artwork would punch holes in it
  colour    multi-coloured artwork on a light background. Measures distance
            from white rather than brightness, because a saturated orange is
            nearly as bright as paper and a luminance rule renders it half
            faded next to a red of the same visual weight.
  knockout  artwork where a light shape sits inside a solid coloured field, and
            transparency carries the rest. Ink is "opaque AND not light", so
            the inner shape stays a hole rather than filling in — an NYU torch
            or a Kroger ellipse flattens to a blob under any other rule.

The result is trimmed to the artwork's bounding box, so the aspect ratio
printed at the end describes the mark rather than whatever padding the source
happened to carry.
"""
import os
import sys

import numpy as np
from PIL import Image

MAX_EDGE = 480


def build_alpha(path, mode):
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im).astype(float)
    rgb, src_alpha = a[..., :3], a[..., 3]
    lum = rgb @ [0.2126, 0.7152, 0.0722]

    if mode == "dark":
        ink = np.clip((235.0 - lum) / 200.0, 0, 1)
        ink *= src_alpha / 255.0
    elif mode == "light":
        ink = np.clip((lum - 20.0) / 200.0, 0, 1)
        ink *= src_alpha / 255.0
    elif mode == "colour":
        # Distance from white via the darkest channel: any saturated hue has at
        # least one low channel, so red, orange and purple all reach full ink
        # while paper stays empty.
        ink = np.clip((255.0 - rgb.min(axis=2)) / 190.0, 0, 1)
        ink *= src_alpha / 255.0
    elif mode == "knockout":
        ink = ((src_alpha > 128) & (lum < 128)).astype(float)
    else:
        raise SystemExit("mode must be dark, light, colour or knockout")
    return ink


def main(src, dest, mode):
    ink = build_alpha(os.path.expanduser(src), mode)

    ys, xs = np.where(ink > 0.08)
    if len(xs) == 0:
        raise SystemExit("no artwork found — wrong mode?")
    ink = ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]

    h, w = ink.shape
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., 3] = (ink * 255).astype(np.uint8)      # RGB stays black; alpha is the mark

    im = Image.fromarray(out, "RGBA")
    im.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    im.save(dest, "WEBP", quality=88, method=6, exact=True)

    print(f"  {os.path.basename(dest):24s} {im.size[0]:3d}x{im.size[1]:<3d} "
          f"aspect {im.size[0]/im.size[1]:.2f}  {os.path.getsize(dest)/1024:5.1f} KB  ({mode})")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2], sys.argv[3])
