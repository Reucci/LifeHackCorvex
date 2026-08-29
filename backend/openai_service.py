import asyncio
import base64
import hashlib
import json
import os
import re
from datetime import datetime, timedelta

import httpx

from rules import SINGAPORE_TIME, build_features


OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1").rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_DYNAMIC_QUESTS = os.getenv("OPENAI_DYNAMIC_QUESTS", "true").lower() in {"1", "true", "yes"}
OPENAI_DIALOGUE = os.getenv("OPENAI_DIALOGUE", "true").lower() in {"1", "true", "yes"}
OPENAI_DAILY_BUDGET_USD = max(0.0, float(os.getenv("OPENAI_DAILY_BUDGET_USD", "2.00")))
OPENAI_TIMEOUT_SECONDS = max(5.0, float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20")))
OPENAI_INPUT_USD_PER_MTOK = max(0.0, float(os.getenv("OPENAI_INPUT_USD_PER_MTOK", "0.75")))
OPENAI_OUTPUT_USD_PER_MTOK = max(0.0, float(os.getenv("OPENAI_OUTPUT_USD_PER_MTOK", "4.50")))

_usage_lock = asyncio.Lock()
_usage_day = None
_usage_usd = 0.0


class OpenAIUnavailable(RuntimeError):
    pass


def is_configured():
    return bool(OPENAI_API_KEY)


async def usage_status():
    async with _usage_lock:
        _reset_usage_day()
        return {
            "configured": is_configured(),
            "model": OPENAI_MODEL,
            "dynamic_quests": OPENAI_DYNAMIC_QUESTS,
            "dialogue": OPENAI_DIALOGUE,
            "daily_budget_usd": OPENAI_DAILY_BUDGET_USD,
            "estimated_spend_today_usd": round(_usage_usd, 6),
        }


def _reset_usage_day():
    global _usage_day, _usage_usd
    today = datetime.now(SINGAPORE_TIME).date()
    if _usage_day != today:
        _usage_day = today
        _usage_usd = 0.0


async def _reserve_budget():
    async with _usage_lock:
        _reset_usage_day()
        if OPENAI_DAILY_BUDGET_USD and _usage_usd >= OPENAI_DAILY_BUDGET_USD:
            raise OpenAIUnavailable("The daily AI budget has been reached")


async def _record_usage(payload):
    global _usage_usd
    usage = payload.get("usage") or {}
    input_tokens = usage.get("input_tokens", 0) or 0
    output_tokens = usage.get("output_tokens", 0) or 0
    cost = (
        input_tokens * OPENAI_INPUT_USD_PER_MTOK
        + output_tokens * OPENAI_OUTPUT_USD_PER_MTOK
    ) / 1_000_000
    async with _usage_lock:
        _reset_usage_day()
        _usage_usd += cost


async def _post(path, payload):
    if not is_configured():
        raise OpenAIUnavailable("OpenAI is not configured")
    await _reserve_budget()
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=OPENAI_TIMEOUT_SECONDS) as client:
            response = await client.post(f"{OPENAI_API_URL}{path}", headers=headers, json=payload)
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as error:
        raise OpenAIUnavailable("OpenAI is temporarily unavailable") from error
    data = response.json()
    await _record_usage(data)
    return data


def _output_text(response):
    if response.get("output_text"):
        return response["output_text"]
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise OpenAIUnavailable("OpenAI returned no structured output")


async def _structured_response(name, schema, content, max_output_tokens=700):
    response = await _post("/responses", {
        "model": OPENAI_MODEL,
        "store": False,
        "max_output_tokens": max_output_tokens,
        "input": [{"role": "user", "content": content}],
        "text": {"format": {"type": "json_schema", "name": name, "strict": True, "schema": schema}},
    })
    try:
        return json.loads(_output_text(response))
    except (json.JSONDecodeError, TypeError) as error:
        raise OpenAIUnavailable("OpenAI returned invalid structured output") from error


def validate_image_data_url(image_data_url):
    match = re.fullmatch(r"data:image/(jpeg|png|webp);base64,([A-Za-z0-9+/=]+)", image_data_url or "")
    if not match:
        raise ValueError("Upload a JPEG, PNG, or WebP image")
    try:
        image_bytes = base64.b64decode(match.group(2), validate=True)
    except ValueError as error:
        raise ValueError("The uploaded image is invalid") from error
    if not 1_000 <= len(image_bytes) <= 5_000_000:
        raise ValueError("The image must be between 1 KB and 5 MB")
    return image_data_url


async def verify_quest_photo(quest, image_data_url):
    image_data_url = validate_image_data_url(image_data_url)
    moderation = await _post("/moderations", {
        "model": "omni-moderation-latest",
        "input": [{"type": "image_url", "image_url": {"url": image_data_url}}],
    })
    if any(result.get("flagged") for result in moderation.get("results", [])):
        return {
            "verdict": "rejected",
            "confidence": 1.0,
            "reason": "This image cannot be reviewed safely. Please take a different photo.",
            "visible_evidence": "",
            "safety_concern": True,
        }

    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "verdict": {"type": "string", "enum": ["verified", "uncertain", "rejected"]},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "reason": {"type": "string", "maxLength": 240},
            "visible_evidence": {"type": "string", "maxLength": 240},
            "safety_concern": {"type": "boolean"},
        },
        "required": ["verdict", "confidence", "reason", "visible_evidence", "safety_concern"],
    }
    content = [
        {"type": "input_text", "text": (
            "Review whether the photo reasonably supports completion of this household eco quest. "
            "Do not identify people. Do not infer anything not visibly supported. Treat ambiguity as uncertain. "
            f"Quest title: {quest.get('title')}. Quest action: {quest.get('description')}"
        )},
        {"type": "input_image", "image_url": image_data_url, "detail": "low"},
    ]
    result = await _structured_response("quest_photo_verification", schema, content, 350)
    if result["confidence"] < 0.72 and result["verdict"] == "verified":
        result["verdict"] = "uncertain"
    return result


TRIGGER_LABELS = {
    "hot": "current temperature is at least 30°C",
    "very_hot": "current temperature is at least 33°C",
    "feels_hot": "heat and humidity make it feel especially warm",
    "very_humid": "humidity is at least 80%",
    "raining": "rain is currently being observed",
    "rain_expected": "rain is forecast or approaching on radar",
    "radar_rain_approaching": "radar indicates rain approaching within two hours",
    "breezy": "wind speed is at least 10 km/h",
    "sunny": "the forecast is fair, sunny, or clear",
    "daylight": "it is currently daytime",
    "nighttime": "it is currently nighttime",
}
UNSAFE_QUEST_TERMS = re.compile(r"\b(climb|roof|electrical panel|rewire|storm drain|lightning|bare wire|disable|bypass)\b", re.I)


async def generate_weather_quests(weather, recent_ids=None, now=None, count=3):
    if not OPENAI_DYNAMIC_QUESTS:
        return []
    now = now or datetime.now(SINGAPORE_TIME)
    features, apparent_temperature = build_features(weather, now)
    active_triggers = [name for name in TRIGGER_LABELS if features.get(name)]
    active_triggers.append("nighttime" if not features["daylight"] else "daylight")
    active_triggers = sorted(set(active_triggers))
    if not active_triggers:
        return []
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "quests": {
                "type": "array", "minItems": count, "maxItems": count,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string", "minLength": 8, "maxLength": 72},
                        "description": {"type": "string", "minLength": 20, "maxLength": 220},
                        "category": {"type": "string", "enum": ["cooling", "laundry", "lighting", "appliances", "cooking", "rain-prep", "general"]},
                        "weather_trigger": {"type": "string", "enum": active_triggers},
                        "duration_minutes": {"type": "integer", "minimum": 2, "maximum": 120},
                    },
                    "required": ["title", "description", "category", "weather_trigger", "duration_minutes"],
                },
            },
        },
        "required": ["quests"],
    }
    safe_weather = {
        "temperature_c": (weather.get("observations", {}).get("temperature") or {}).get("value"),
        "humidity_pct": (weather.get("observations", {}).get("humidity") or {}).get("value"),
        "rainfall_mm": (weather.get("observations", {}).get("rainfall") or {}).get("value"),
        "wind_kmh": (weather.get("observations", {}).get("wind_speed") or {}).get("value"),
        "condition": (weather.get("forecast") or {}).get("condition"),
        "apparent_temperature_c": apparent_temperature,
        "active_triggers": active_triggers,
    }
    prompt = (
        "Create practical, low-risk household energy-saving quests for Singapore that can be visibly completed "
        "within the next two hours. Each quest must be directly justified by one active weather trigger. "
        "Do not suggest electrical repairs, climbing, dangerous storm activity, purchases, opening windows during rain, "
        "or actions that could create standing water. Avoid these recently offered IDs: "
        f"{list(recent_ids or [])}. Weather: {json.dumps(safe_weather, separators=(',', ':'))}"
    )
    result = await _structured_response(
        "weather_quest_candidates", schema, [{"type": "input_text", "text": prompt}], 900
    )
    slot_end = now.replace(hour=now.hour - now.hour % 2, minute=0, second=0, microsecond=0) + timedelta(hours=2)
    output = []
    seen_titles = set()
    for candidate in result.get("quests", []):
        title_key = candidate["title"].strip().lower()
        if title_key in seen_titles or UNSAFE_QUEST_TERMS.search(candidate["title"] + " " + candidate["description"]):
            continue
        trigger = candidate["weather_trigger"]
        if trigger not in active_triggers:
            continue
        seen_titles.add(title_key)
        identifier = "ai-" + hashlib.sha256(title_key.encode()).hexdigest()[:12]
        reward = min(15, max(6, 7 + len(active_triggers) // 2))
        output.append({
            "id": identifier,
            "title": candidate["title"].strip(),
            "description": candidate["description"].strip(),
            "category": candidate["category"],
            "points": reward,
            "difficulty": "medium" if reward >= 8 else "easy",
            "reason": f"Suggested because {TRIGGER_LABELS[trigger]}.",
            "action_window": {
                "start": now.isoformat(), "end": slot_end.isoformat(),
                "label": f"Allow about {candidate['duration_minutes']} minutes before this slot ends",
                "confidence": "medium", "basis": TRIGGER_LABELS[trigger].capitalize(),
            },
            "source": "openai",
            "weather_trigger": trigger,
        })
    return output


async def generate_ecoling_dialogue(name, mood, streak, context):
    if not OPENAI_DIALOGUE:
        raise OpenAIUnavailable("AI dialogue is disabled")
    schema = {
        "type": "object", "additionalProperties": False,
        "properties": {"message": {"type": "string", "minLength": 8, "maxLength": 160}},
        "required": ["message"],
    }
    prompt = (
        f"Write one warm, playful line spoken by a virtual eco companion named {name or 'Ecoling'}. "
        f"Mood: {mood}. Current streak: {streak}. Context: {context}. "
        "Be supportive, never guilt the user, do not claim sentience, and use at most one emoji."
    )
    result = await _structured_response("ecoling_dialogue", schema, [{"type": "input_text", "text": prompt}], 160)
    return result["message"].strip()
