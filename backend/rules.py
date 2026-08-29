# Select one safe, weather-relevant energy quest for Singapore

from datetime import datetime, timedelta, timezone
import random


RAIN_TERMS = ("rain", "shower", "thunder")
SUN_TERMS = ("fair", "sunny", "clear")
SINGAPORE_TIME = timezone(timedelta(hours=8))

QUESTS = [
    {
        "id": "bring-laundry-in-before-rain",
        "title": "Bring drying laundry in before the rain",
        "description": "Protect a naturally dried load now so you do not need to run the dryer again.",
        "category": "laundry",
        "base_points": 20,
        "requires": {"daylight": True, "radar_rain_approaching": True},
        "bonuses": {"radar_high_confidence": 4},
        "urgent": True,
    },
    {
        "id": "line-dry-clothes",
        "title": "Line-dry one load of laundry",
        "description": "Use today's dry conditions instead of running the dryer.",
        "category": "laundry",
        "base_points": 18,
        "requires": {"daylight": True, "raining": False, "rain_expected": False},
        "bonuses": {"breezy": 5, "sunny": 3},
    },
    {
        "id": "close-sun-facing-blinds",
        "title": "Close sun-facing blinds",
        "description": "Block afternoon heat before it enters your room and reduce AC demand.",
        "category": "cooling",
        "base_points": 14,
        "requires": {"daylight": True, "hot": True},
        "bonuses": {"sunny": 4, "very_hot": 4},
    },
    {
        "id": "fan-first",
        "title": "Try a fan before switching on the AC",
        "description": "Run a fan for 20 minutes first and only use AC if you still need it.",
        "category": "cooling",
        "base_points": 12,
        "requires": {"raining": False, "comfortable_for_fan": True},
        "bonuses": {"breezy": 3},
    },
    {
        "id": "efficient-ac-setting",
        "title": "Keep the AC at 25°C or warmer",
        "description": "Use an efficient setting and keep doors and windows closed while cooling.",
        "category": "cooling",
        "base_points": 16,
        "requires": {"feels_hot": True},
        "bonuses": {"very_hot": 4, "very_humid": 3},
    },
    {
        "id": "natural-daylight",
        "title": "Use daylight instead of room lights",
        "description": "Work near a window and switch off unnecessary lights for one hour.",
        "category": "lighting",
        "base_points": 9,
        "requires": {"daylight": True},
        "bonuses": {"sunny": 4},
    },
    {
        "id": "delay-heavy-appliances",
        "title": "Delay one heat-producing appliance",
        "description": "Avoid the oven or dryer during the hottest part of the day.",
        "category": "appliances",
        "base_points": 12,
        "requires": {"daylight": True, "hot": True},
        "bonuses": {"very_hot": 4},
    },
    {
        "id": "rainy-day-standby",
        "title": "Switch off idle devices at the socket",
        "description": "Use this indoor rainy-day quest to cut standby electricity use.",
        "category": "appliances",
        "base_points": 10,
        "requires": {"rain_context": True},
        "bonuses": {"raining": 4, "rain_expected": 2},
    },
    {
        "id": "unplug-idle-devices",
        "title": "Unplug three idle devices",
        "description": "Disconnect chargers or electronics that are not being used.",
        "category": "appliances",
        "base_points": 8,
        "requires": {},
        "bonuses": {},
    },
]


def _value(weather, name):
    observation = weather["observations"].get(name)
    return observation["value"] if observation else None


def build_features(weather, now=None):
    now = now or datetime.now(SINGAPORE_TIME)
    temperature = float(_value(weather, "temperature"))
    humidity = _value(weather, "humidity")
    humidity = float(humidity) if humidity is not None else None
    rainfall = _value(weather, "rainfall")
    rainfall = float(rainfall) if rainfall is not None else 0
    wind_speed = _value(weather, "wind_speed")
    wind_speed = float(wind_speed) if wind_speed is not None else 0
    condition = (weather.get("forecast") or {}).get("condition", "").lower()
    radar = weather.get("radar") or {}
    radar_rain_approaching = (
        radar.get("movement") == "approaching"
        and radar.get("eta_minutes") is not None
        and radar["eta_minutes"] <= 120
    )

    apparent_temperature = temperature
    if humidity is not None and temperature >= 27:
        apparent_temperature += max(0, humidity - 60) * 0.04

    raining = rainfall > 0
    rain_expected = any(term in condition for term in RAIN_TERMS) or radar_rain_approaching
    features = {
        "daylight": 7 <= now.hour < 19,
        "hot": temperature >= 30,
        "very_hot": temperature >= 33,
        "very_humid": humidity is not None and humidity >= 80,
        "feels_hot": apparent_temperature >= 31,
        "comfortable_for_fan": temperature < 31 and apparent_temperature < 33,
        "raining": raining,
        "rain_expected": rain_expected,
        "rain_context": raining or rain_expected,
        "breezy": wind_speed >= 10,
        "sunny": any(term in condition for term in SUN_TERMS),
        "radar_rain_approaching": radar_rain_approaching,
        "radar_high_confidence": radar.get("confidence") == "high",
    }
    return features, round(apparent_temperature, 1)


def choose_quests(weather, count=2, seed=None, now=None):
    """Return distinct, weighted-random choices from the best eligible quests."""
    features, apparent_temperature = build_features(weather, now)
    candidates = []

    for quest in QUESTS:
        if any(features.get(name) is not expected for name, expected in quest["requires"].items()):
            continue
        score = quest["base_points"]
        score += sum(points for name, points in quest["bonuses"].items() if features.get(name))
        candidates.append((score, quest))

    # Keep randomization relevant: sample from the five strongest eligible
    # candidates, with stronger weather matches more likely to be offered.
    pool = sorted(candidates, key=lambda item: item[0], reverse=True)[:5]
    rng = random.Random(seed)
    selected_options = []
    urgent = next((item for item in pool if item[1].get("urgent")), None)
    if urgent:
        pool.remove(urgent)
        selected_options.append(_format_quest(*urgent, weather, features, apparent_temperature, now))
    while pool and len(selected_options) < count:
        minimum = min(score for score, _ in pool)
        weights = [score - minimum + 2 for score, _ in pool]
        chosen_index = rng.choices(range(len(pool)), weights=weights, k=1)[0]
        raw_score, selected = pool.pop(chosen_index)
        selected_options.append(
            _format_quest(raw_score, selected, weather, features, apparent_temperature, now)
        )
    return selected_options


def choose_quest(weather, now=None):
    """Compatibility helper for callers that need a single quest."""
    return choose_quests(weather, count=1, now=now)[0]


def _format_quest(raw_score, selected, weather, features, apparent_temperature, now):
    reward = max(4, min(15, round(raw_score * 0.6)))
    difficulty = "hard" if reward >= 12 else "medium" if reward >= 8 else "easy"
    return {
        "id": selected["id"],
        "title": selected["title"],
        "description": selected["description"],
        "category": selected["category"],
        "points": reward,
        "difficulty": difficulty,
        "reason": _weather_reason(weather, features, apparent_temperature),
        "action_window": _predict_action_window(selected["id"], weather, features, now),
    }


def _predict_action_window(quest_id, weather, features, now):
    now = now or datetime.now(SINGAPORE_TIME)
    slot_end = now.replace(hour=now.hour - now.hour % 2, minute=0, second=0, microsecond=0) + timedelta(hours=2)
    radar = weather.get("radar") or {}
    confidence = radar.get("confidence", "medium")

    if quest_id == "bring-laundry-in-before-rain" and radar.get("eta_minutes"):
        safe_minutes = max(5, radar["eta_minutes"] - 10)
        end = min(slot_end, now + timedelta(minutes=safe_minutes))
        return {
            "start": now.isoformat(),
            "end": end.isoformat(),
            "label": f"Act within {safe_minutes} minutes, before the rain echo may arrive",
            "confidence": confidence,
            "basis": f"Radar estimates nearby rain in about {radar['eta_minutes']} minutes",
        }

    if quest_id in {"close-sun-facing-blinds", "delay-heavy-appliances"} and features["hot"]:
        end = min(slot_end, now + timedelta(minutes=30))
        return {
            "start": now.isoformat(),
            "end": end.isoformat(),
            "label": "Best in the next 30 minutes, before more heat builds indoors",
            "confidence": "medium",
            "basis": "Current heat makes prevention more efficient than cooling later",
        }

    if radar.get("movement") == "moving_away":
        return {
            "start": now.isoformat(),
            "end": slot_end.isoformat(),
            "label": "Good anytime in this slot; nearby rain is moving away",
            "confidence": confidence,
            "basis": "Recent radar frames show the nearest rain echo receding",
        }

    return {
        "start": now.isoformat(),
        "end": slot_end.isoformat(),
        "label": "Complete anytime before this two-hour slot ends",
        "confidence": "medium",
        "basis": "Current observations and the two-hour area forecast agree with this quest",
    }


def _weather_reason(weather, features, apparent_temperature):
    temperature = _value(weather, "temperature")
    area = (weather.get("forecast") or {}).get("area", "your area")
    condition = (weather.get("forecast") or {}).get("condition")
    radar = weather.get("radar") or {}
    if features["radar_rain_approaching"]:
        return f"Three recent radar frames indicate rain may reach {area} in about {radar['eta_minutes']} minutes."
    if features["raining"]:
        return f"Rain is being observed near {area}, so an indoor quest is safest."
    if features["rain_expected"]:
        return f"The two-hour forecast for {area} is {condition}; this quest stays weather-safe."
    if features["feels_hot"]:
        return f"It is {temperature}°C and feels about {apparent_temperature}°C near you."
    return f"The nearest official station reports {temperature}°C near {area}."
