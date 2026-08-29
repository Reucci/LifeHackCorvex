"""Converts a weather reading into "quests": electricity-saving suggestions."""

import math
import re

CONDITIONS = {"clear", "clouds", "rain", "snow", "wind", "fog", "storm"}

PRIORITY_VALUE = {"high": 3, "medium": 2, "low": 1}


def calculate_gold(priority, temp_c=None, threshold=None):
    """Gold reward for completing a quest of the given priority.

    For quests tied to a heat threshold (e.g. "use a fan" only applies once
    it's at least 24°C), the reward scales with how far past that threshold
    the actual temperature is:

        gold = 10 * value + log_1.5(temp_c - threshold)

    e.g. completing a quest at 26°C that only unlocks at 24°C gives
    10 * value + log_1.5(26 - 24). Right at the threshold (or with no
    threshold given), the log term drops to 0 for temp_c == threshold, or
    falls back to log_1.5(value) when no threshold applies at all.
    """
    if priority not in PRIORITY_VALUE:
        raise ValueError(f"unknown priority: {priority}")
    value = PRIORITY_VALUE[priority]

    if threshold is not None and temp_c is not None:
        delta = temp_c - threshold
        bonus = math.log(delta, 1.5) if delta > 0 else 0.0
    else:
        bonus = math.log(value, 1.5)

    return 10 * value + bonus


def to_celsius(temp, unit):
    if unit == "F":
        return (temp - 32) * 5 / 9
    return temp  # already Celsius


def normalize_condition(condition):
    c = str(condition or "").lower().strip()
    if c in CONDITIONS:
        return c
    if re.search(r"(sun|clear)", c):
        return "clear"
    if re.search(r"(cloud|overcast)", c):
        return "clouds"
    if re.search(r"(rain|drizzle|shower)", c):
        return "rain"
    if re.search(r"(snow|sleet|blizzard)", c):
        return "snow"
    if re.search(r"(wind|breez|gale)", c):
        return "wind"
    if re.search(r"(fog|mist|haze)", c):
        return "fog"
    if re.search(r"(storm|thunder)", c):
        return "storm"
    return "unknown"


def _quest(id_, title, description, category, priority, temp_c=None, threshold=None):
    gold = calculate_gold(priority, temp_c=temp_c, threshold=threshold)
    return {
        "id": id_,
        "title": title,
        "description": description,
        "category": category,
        "priority": priority,
        "gold": round(gold, 2),
    }


def get_quests(temperature, unit="C", condition=None, humidity=None, wind_speed=None):
    """
    :param temperature: number
    :param unit: "C" or "F"
    :param condition: free text, e.g. "clear", "rain", "snow", "cloudy", "windy", "storm"
    :param humidity: percentage 0-100
    :param wind_speed: km/h
    """
    unit = (unit or "C").upper()

    try:
        temp_value = float(temperature)
    except (TypeError, ValueError):
        raise ValueError("temperature must be a number")

    temp_c = to_celsius(temp_value, unit)
    condition_norm = normalize_condition(condition)
    humidity_value = float(humidity) if humidity is not None else None
    wind_speed_value = float(wind_speed) if wind_speed is not None else None

    quests = []

    # --- Temperature band suggestions ---
    if temp_c < 20:
        quests.append(_quest(
            "ac-off-cold",
            "Turn off the air conditioning",
            "It's chilly - the AC isn't needed. Turn it off to save power.",
            "cooling", "high",
        ))
        quests.append(_quest(
            "layer-up",
            "Layer up instead of heating",
            "Put on a sweater or blanket before reaching for the heater.",
            "heating", "medium",
        ))
        quests.append(_quest(
            "seal-drafts",
            "Close windows and doors",
            "Keep the cold air out so any heating you do use works efficiently.",
            "heating", "low",
        ))
    elif temp_c < 24:
        quests.append(_quest(
            "hvac-off-mild",
            "Turn off heating and AC",
            "The temperature is comfortable as-is - no climate control needed.",
            "hvac", "high",
        ))
        quests.append(_quest(
            "natural-ventilation",
            "Open a window",
            "Let in fresh air instead of running the AC or fans.",
            "cooling", "medium",
        ))
    elif temp_c < 28:
        quests.append(_quest(
            "fan-over-ac",
            "Use a fan instead of the AC",
            "It's warm but not extreme - a fan uses a fraction of the power an AC does.",
            "cooling", "high", temp_c=temp_c, threshold=24,
        ))
        quests.append(_quest(
            "close-blinds",
            "Close blinds or curtains",
            "Block direct sunlight to keep the room cooler without more cooling power.",
            "cooling", "medium", temp_c=temp_c, threshold=24,
        ))
    else:
        quests.append(_quest(
            "ac-efficient-temp",
            "Set the AC to 24-26°C (75-78°F)",
            "It's hot - the AC is warranted, but every degree colder adds ~3-5% more energy use.",
            "cooling", "high", temp_c=temp_c, threshold=28,
        ))
        quests.append(_quest(
            "avoid-oven",
            "Avoid the oven and heat-generating appliances",
            "Cooking with an oven heats the room, making the AC work harder.",
            "cooling", "medium", temp_c=temp_c, threshold=28,
        ))
        quests.append(_quest(
            "close-blinds-hot",
            "Close blinds during peak sun",
            "Reduce solar heat gain so the AC doesn't have to work as hard.",
            "cooling", "medium", temp_c=temp_c, threshold=28,
        ))

    # --- Condition-based suggestions ---
    if condition_norm == "clear":
        quests.append(_quest(
            "natural-light",
            "Turn off the lights",
            "It's sunny - rely on natural daylight instead of electric lighting.",
            "lighting", "medium",
        ))
    elif condition_norm in ("clouds", "fog"):
        quests.append(_quest(
            "moderate-hvac",
            "Ease off heating/cooling",
            "Overcast skies keep temperatures moderate - check if you even need climate control right now.",
            "hvac", "low",
        ))
    elif condition_norm in ("rain", "storm"):
        if temp_c >= 20 and humidity_value is not None and humidity_value < 70:
            quests.append(_quest(
                "rain-cooling",
                "Let the rain cool things down",
                "Rain often drops the ambient temperature - try opening a window before switching on the AC.",
                "cooling", "medium",
            ))
        quests.append(_quest(
            "unplug-electronics-storm",
            "Unplug sensitive electronics",
            "Storms can bring power surges - unplugging idle electronics also cuts phantom load.",
            "safety", "low",
        ))
    elif condition_norm == "snow":
        quests.append(_quest(
            "insulate-heat",
            "Insulate instead of over-heating",
            "Use draft stoppers and rugs to retain heat rather than raising the thermostat.",
            "heating", "medium",
        ))
    elif condition_norm == "wind" or (wind_speed_value is not None and wind_speed_value > 20):
        quests.append(_quest(
            "wind-ventilation",
            "Use the breeze instead of a fan",
            "Strong wind can ventilate a room on its own - crack a window instead of running a fan.",
            "cooling", "medium",
        ))

    # --- Humidity-based suggestions ---
    if humidity_value is not None:
        if humidity_value > 70 and temp_c >= 20:
            quests.append(_quest(
                "dehumidify-not-cool",
                "Use a dehumidifier instead of lowering the AC temp",
                "High humidity makes it feel hotter - dehumidifying is cheaper than over-cooling.",
                "cooling", "medium",
            ))
        elif humidity_value < 30 and temp_c < 15:
            quests.append(_quest(
                "humidifier-comfort",
                "Add a humidifier instead of raising the heat",
                "Dry air feels colder than it is - humidifying can let you lower the thermostat.",
                "heating", "low",
            ))

    # Always-applicable low-priority tip
    quests.append(_quest(
        "unplug-idle",
        "Unplug idle devices",
        "Chargers and electronics draw phantom power even when off - unplug what you're not using.",
        "general", "low",
    ))

    quests.sort(key=lambda q: PRIORITY_VALUE[q["priority"]], reverse=True)

    return {
        "weather": {
            "temperature": temp_value,
            "unit": unit,
            "temperatureCelsius": round(temp_c, 1),
            "condition": condition_norm,
            "humidity": humidity_value,
            "windSpeed": wind_speed_value,
        },
        "quests": quests,
    }
