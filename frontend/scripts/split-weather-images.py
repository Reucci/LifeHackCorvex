"""Slice a 2x2 weather-mood grid image into the four backgrounds the app expects.

Usage:
    python scripts/split-weather-images.py path/to/grid.png

Grid layout (matches the reference art):
    top-left     -> weather-sunny.png      (clear / sunny)
    bottom-left  -> weather-partly.png     (partly cloudy)
    top-right    -> weather-overcast.png   (grey / overcast)
    bottom-right -> weather-rainy.png      (rain)

Output goes to frontend/public/images/. Tweak MARGIN if the source has a
border/gutter around each tile (the reference art has a small cream gutter).
"""

import sys
from pathlib import Path

from PIL import Image

MARGIN = 0.03  # fraction of each tile trimmed off as gutter; set 0 for a clean grid

OUT_DIR = Path(__file__).resolve().parent.parent / "public" / "images"

# (row, col) -> output filename
TILES = {
    (0, 0): "weather-sunny.png",
    (1, 0): "weather-partly.png",
    (0, 1): "weather-overcast.png",
    (1, 1): "weather-rainy.png",
}


def main() -> None:
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    src = Image.open(sys.argv[1]).convert("RGB")
    w, h = src.size
    tile_w, tile_h = w / 2, h / 2
    mx, my = tile_w * MARGIN, tile_h * MARGIN

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for (row, col), name in TILES.items():
        left = col * tile_w + mx
        upper = row * tile_h + my
        right = (col + 1) * tile_w - mx
        lower = (row + 1) * tile_h - my
        crop = src.crop((round(left), round(upper), round(right), round(lower)))
        dest = OUT_DIR / name
        crop.save(dest)
        print(f"wrote {dest}  ({crop.width}x{crop.height})")


if __name__ == "__main__":
    main()
