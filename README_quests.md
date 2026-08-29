# weather-to-quest-api (Python)

Takes a weather reading and returns "quests" — suggestions for saving electricity
(e.g. chilly out → turn off the AC).

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Server listens on `http://localhost:3000`.

## Endpoint

`POST /api/quest`

Request body:

```json
{
  "temperature": 8,
  "unit": "C",
  "condition": "clear",
  "humidity": 40,
  "windSpeed": 5
}
```

- `temperature` (required): number
- `unit`: `"C"` or `"F"` (default `"C"`)
- `condition`: free text, e.g. `"clear"`, `"rain"`, `"snow"`, `"cloudy"`, `"windy"`, `"storm"`
- `humidity`: percentage 0-100 (optional)
- `windSpeed`: km/h (optional)

Response:

```json
{
  "weather": { "temperature": 8, "unit": "C", "temperatureCelsius": 8, "condition": "clear", "humidity": null, "windSpeed": null },
  "quests": [
    { "id": "ac-off-cold", "title": "Turn off the air conditioning", "description": "...", "category": "cooling", "priority": "high", "gold": 32.71 }
  ]
}
```

Quests are sorted highest-priority-first. Each quest carries a `gold` reward for completing it,
based on its priority:

| priority | value | gold = 10 * value + log₁.₅(value) |
|----------|-------|------------------------------------|
| high     | 3     | 32.71                              |
| medium   | 2     | 21.71                              |
| low      | 1     | 10.0                                |

**Heat-threshold bonus:** for quests that only unlock past a heat threshold — `fan-over-ac` /
`close-blinds` (unlock at 24°C), and `ac-efficient-temp` / `avoid-oven` / `close-blinds-hot`
(unlock at 28°C) — the reward instead scales with how far past that threshold the actual
temperature is:

```
gold = 10 * value + log₁.₅(temp_c - threshold)
```

e.g. completing `fan-over-ac` (value 3, threshold 24°C) at an actual 26°C gives
`10 * 3 + log₁.₅(26 - 24) = 30 + 1.71 = 31.71` gold — hotter weather earns more gold for the
same quest. Right at the threshold the bonus is 0 (just the base `10 * value`). Quests with no
heat threshold (condition-, humidity-, and general-based ones) keep the flat
`10 * value + log₁.₅(value)` formula above.

A `GET /api/quest?temperature=8&unit=C&condition=rain` variant is also available for quick manual testing.

`POST /api/quest/complete`

Request body:

```json
{ "priority": "high" }
```

Response:

```json
{ "priority": "high", "gold": 32.71 }
```

## Test

```bash
pip install pytest
pytest
```
