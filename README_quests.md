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
    { "id": "ac-off-cold", "title": "Turn off the air conditioning", "description": "...", "category": "cooling", "priority": "high", "gold": 33 }
  ]
}
```

Quests are sorted highest-priority-first. Each quest carries a `gold` reward (an integer) for
completing it, based on its priority:

| priority | value | gold = round(10 * value + log₁.₅(value)) |
|----------|-------|--------------------------------------------|
| high     | 3     | 33                                          |
| medium   | 2     | 22                                          |
| low      | 1     | 10                                          |

**Heat-threshold bonus:** for quests that only unlock past a heat threshold — `fan-over-ac` /
`close-blinds` (unlock at 24°C), and `ac-efficient-temp` / `avoid-oven` / `close-blinds-hot`
(unlock at 28°C) — the reward instead scales with how far past that threshold the actual
temperature is:

```
gold = round(10 * value + log₁.₅(temp_c - threshold))
```

e.g. completing `fan-over-ac` (value 3, threshold 24°C) at an actual 26°C gives
`round(10 * 3 + log₁.₅(26 - 24)) = round(30 + 1.71) = 32` gold — hotter weather earns more gold
for the same quest. Right at the threshold the bonus is 0 (just the base `10 * value`). Quests
with no heat threshold (condition-, humidity-, and general-based ones) keep the flat
`round(10 * value + log₁.₅(value))` formula above.

A `GET /api/quest?temperature=8&unit=C&condition=rain` variant is also available for quick manual testing.

`POST /api/quest/complete`

Request body:

```json
{ "priority": "high", "user_id": "zach" }
```

`user_id` is optional. Without it you just get quest pricing back. With it, the completion is
also recorded against that user's persisted streak (see below) and any newly-earned awards are
returned.

Response (with `user_id`):

```json
{
  "priority": "high",
  "gold": 33,
  "user_id": "zach",
  "streak": 1,
  "daily_streak": 1,
  "total_completed": 1,
  "awards_earned": [
    { "award_id": 3, "award_name": "First Quest", "award_type": "first_quest", "gold_reward": 10.0 }
  ]
}
```

`POST /api/quest/miss`

Breaks a user's consecutive-quest streak back to 0 (their daily streak and lifetime total, and
any awards already earned, are untouched):

```json
{ "user_id": "zach" }
```

## Database & awards (db.py, models.py, awards_service.py)

Quest completions and awards are persisted with SQLAlchemy (SQLite by default,
`ECOLINGS_DATABASE_URL` to point elsewhere):

- **`db.py`** — engine/session/`Base` setup.
- **`models.py`** — `Product` (a redemption-shop catalog: `product_id`, `product_name`,
  `product_stock`, `product_desc`, `product_cost`), `Award` (the catalog of awards, with
  `award_type` + `threshold`, e.g. `streak`/50, `daily_streak`/14, `first_quest`/1),
  `UserStreak` (per-user `current_streak`, `daily_streak`, `total_completed`,
  `last_completed_date`), and `UserAward` (one row per award actually granted, so nothing is
  double-awarded).
- **`awards_service.py`** — the glue: `record_completion(session, user_id)` bumps a user's
  streak/daily-streak/total, checks the `awards` catalog for a newly-crossed threshold, and
  grants any match; `reset_streak(session, user_id)` backs the consecutive-quest streak to 0;
  `seed_default_awards(session)` inserts the three default awards (50-streak, 14-day streak,
  first quest) if they aren't already there. `app.py` calls `seed_default_awards` once at
  startup and opens a `SessionLocal()` per request in the `/api/quest/complete` and
  `/api/quest/miss` routes above.

The 50-streak award's `gold_reward` is computed straight from `streak.py`'s
`calculate_streak_bonus(50)`, so the two stay in sync.

## Streak achievements (streak.py)

`streak.py` is the standalone streak-counting/achievement logic that `awards_service.py` wires
into the database above. Used on its own (no DB), it tracks quests completed back-to-back and
hands out a one-time **achievement** every time the streak reaches a new multiple of 10.

```python
from streak import StreakTracker

tracker = StreakTracker()
for _ in range(10):
    streak, achievement = tracker.complete_quest()

streak       # 10
achievement  # {"streak": 10, "title": "10-Quest Streak", "bonus": 50.0}
             # - only the completion that lands on a NEW multiple of 10 returns one;
             # every other call gets achievement = None

tracker.miss_quest()  # skipped/missed a quest -> streak resets to 0

# climbing back to 10 doesn't re-award the achievement - it's already been earned
for _ in range(10):
    streak, achievement = tracker.complete_quest()
achievement  # None
```

Achievement bonus, for the nth ten-streak reached (`n = streak // 10`):

```
bonus = 50 * n + log₁.₅(n)
```

| streak | n | title              | bonus  |
|--------|---|--------------------|--------|
| 10     | 1 | "10-Quest Streak"  | 50.0   |
| 20     | 2 | "20-Quest Streak"  | 101.71 |
| 30     | 3 | "30-Quest Streak"  | 152.71 |

Earned milestones live in `tracker.achieved_milestones` and are permanent for that tracker -
breaking and rebuilding a streak never re-awards an achievement already earned.

## Test

```bash
pip install pytest
pytest
```
