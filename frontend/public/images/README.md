# Images

## Weather backgrounds

`App.jsx` swaps the app background based on the live weather category
(`utils/weather.js` maps WMO weather codes to one of four "moods").
It expects these files in this folder:

| File                    | When it shows                                  |
| ----------------------- | ---------------------------------------------- |
| `weather-sunny.png`     | clear / mainly clear                           |
| `weather-partly.png`    | partly cloudy                                  |
| `weather-overcast.png`  | overcast, fog, snow                            |
| `weather-rainy.png`     | drizzle, rain, showers, thunderstorm           |

The files in this folder are **generated** — the source art is a portrait crop
(~620x690, framing trees at the left/right edges) that gets extended downward so
the scene fills a tall phone frame. If a file is missing, the per-mood colour in
`.weather-bg--*` (`css/App.css`) still renders on its own.

Pipeline:

1. Put the untouched source art in `scripts/weather-originals/`. To slice a
   single 2x2 grid image into the four moods first:
   ```
   python scripts/split-weather-images.py path/to/grid.png
   ```
   (then move its output into `scripts/weather-originals/`)
2. Extend them to fill the frame (safe to re-run / re-tune the constants at the
   top of the script):
   ```
   python scripts/extend-weather-images.py
   ```
