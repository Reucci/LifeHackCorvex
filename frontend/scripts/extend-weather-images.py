"""Extend each weather background downward so the forest scene fills a tall
phone frame instead of stopping partway.

The top of the art is kept exactly as-is; the bottom foreground band (grass /
undergrowth, which has no strong vertical structure) is stretched vertically to
make up the extra height, then a gentle downward gradient eases it into shadow.
No blur, no mirror. Untouched originals live in scripts/weather-originals/ and
are always used as the source, so the script is safe to re-run and re-tune.

Usage:
    python scripts/extend-weather-images.py
"""

from pathlib import Path

from PIL import Image

IMAGES = Path(__file__).resolve().parent.parent / "public" / "images"
SOURCE = Path(__file__).resolve().parent / "weather-originals"
MOODS = ["sunny", "partly", "overcast", "rainy"]

TARGET_ASPECT = 0.6      # final width:height (portrait phone-ish)
KEEP_FRAC = 0.72         # top fraction of the original kept unscaled
FLOOR_DARKEN = 0.5       # darkness added at the very bottom (0..1)


def darken(img: Image.Image, seam_frac: float) -> Image.Image:
    """Multiply a clear->dark vertical gradient over `img`, starting at seam."""
    w, h = img.size
    ramp = Image.new("L", (1, h))
    start = seam_frac * h
    peak = round(255 * FLOOR_DARKEN)
    for i in range(h):
        t = 0.0 if i <= start else min(1.0, (i - start) / max(1.0, h - start))
        ramp.putpixel((0, i), round(peak * (t ** 1.3)))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(black, img, ramp.resize((w, h)))


def main() -> None:
    SOURCE.mkdir(exist_ok=True)

    for mood in MOODS:
        path = IMAGES / f"weather-{mood}.png"
        if not path.exists():
            print(f"skip {mood}: {path.name} not found")
            continue

        backup = SOURCE / f"weather-{mood}.png"
        base = Image.open(backup if backup.exists() else path).convert("RGB")
        if not backup.exists():
            base.save(backup)

        w, h = base.size
        target_h = max(h, round(w / TARGET_ASPECT))
        if target_h <= h:
            print(f"{mood}: already tall enough ({w}x{h})")
            continue

        keep_h = int(h * KEEP_FRAC)
        top = base.crop((0, 0, w, keep_h))
        bottom = base.crop((0, keep_h, w, h))
        bottom = bottom.resize((w, target_h - keep_h), Image.LANCZOS)

        out = Image.new("RGB", (w, target_h))
        out.paste(top, (0, 0))
        out.paste(bottom, (0, keep_h))
        out = darken(out, keep_h / target_h)

        out.save(path)
        print(f"{mood}: {w}x{h} -> {w}x{target_h}")


if __name__ == "__main__":
    main()
