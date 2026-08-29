# Read weather data and determine quest

import asyncio
import math
import time
from datetime import datetime, timezone

import httpx

from radar_service import get_radar_analysis, RadarUnavailableError


API_ROOT = "https://api-open.data.gov.sg/v2/real-time/api" # Data from gov api
CACHE_SECONDS = 240
MAX_OBSERVATION_AGE_MINUTES = 30

FEEDS = {
    "temperature": ("air-temperature", "°C"),
    "humidity": ("relative-humidity", "%"),
    "rainfall": ("rainfall", "mm"),
    "wind_speed": ("wind-speed", "km/h"),
}

_cache = {}


class WeatherUnavailableError(RuntimeError):
    pass


def haversine_km(lat1, lon1, lat2, lon2):
    radius_km = 6371.0
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def _validate_singapore_location(latitude, longitude):
    if not (1.15 <= latitude <= 1.48 and 103.58 <= longitude <= 104.10):
        raise ValueError("Location must be within Singapore")


async def _fetch_json(client, endpoint):
    now = time.monotonic()
    cached = _cache.get(endpoint)
    if cached and now - cached[0] < CACHE_SECONDS:
        return cached[1]

    last_error = None
    for attempt in range(2):
        try:
            if attempt:
                await asyncio.sleep(0.35)
            response = await client.get(f"{API_ROOT}/{endpoint}")
            response.raise_for_status()
            payload = response.json()
            data = payload.get("data")
            readings_missing = endpoint != "two-hr-forecast" and not (data or {}).get("readings")
            if payload.get("code") != 0 or not data or readings_missing:
                raise WeatherUnavailableError(payload.get("errorMsg") or "Weather data unavailable")
            _cache[endpoint] = (time.monotonic(), data)
            return data
        except (httpx.HTTPError, ValueError, WeatherUnavailableError) as error:
            last_error = error

    # Official real time feeds have short gaps, timestamp is cached an payload is still checked and surfaced as stale to the user
    if cached:
        return cached[1]
    raise last_error


def _parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _age_minutes(timestamp):
    observed_at = _parse_timestamp(timestamp)
    return max(0, round((datetime.now(timezone.utc) - observed_at).total_seconds() / 60, 1))


def _nearest_station_observation(data, latitude, longitude, unit):
    if not data.get("readings"):
        raise WeatherUnavailableError("No current weather readings")

    latest = data["readings"][-1]
    values = {item["stationId"]: item["value"] for item in latest.get("data", [])}
    candidates = []
    for station in data.get("stations", []):
        if station["id"] not in values:
            continue
        location = station["location"]
        distance = haversine_km(
            latitude, longitude, location["latitude"], location["longitude"]
        )
        candidates.append((distance, station, values[station["id"]]))

    if not candidates:
        raise WeatherUnavailableError("No nearby station has a current reading")

    distance, station, value = min(candidates, key=lambda item: item[0])
    age = _age_minutes(latest["timestamp"])
    return {
        "value": value,
        "unit": unit,
        "observed_at": latest["timestamp"],
        "age_minutes": age,
        "is_stale": age > MAX_OBSERVATION_AGE_MINUTES,
        "station": {
            "id": station["id"],
            "name": station["name"],
            "distance_km": round(distance, 2),
            "latitude": station["location"]["latitude"],
            "longitude": station["location"]["longitude"],
        },
    }


def _nearest_forecast(data, latitude, longitude):
    if not data.get("items"):
        raise WeatherUnavailableError("No current two-hour forecast")

    item = data["items"][-1]
    forecasts = {entry["area"]: entry["forecast"] for entry in item["forecasts"]}
    candidates = []
    for area in data.get("area_metadata", []):
        if area["name"] not in forecasts:
            continue
        location = area["label_location"]
        distance = haversine_km(
            latitude, longitude, location["latitude"], location["longitude"]
        )
        candidates.append((distance, area))

    if not candidates:
        raise WeatherUnavailableError("No nearby forecast area")

    distance, area = min(candidates, key=lambda candidate: candidate[0])
    return {
        "area": area["name"],
        "condition": forecasts[area["name"]],
        "distance_km": round(distance, 2),
        "updated_at": item["update_timestamp"],
        "valid_from": item["valid_period"]["start"],
        "valid_to": item["valid_period"]["end"],
    }


async def get_weather(latitude, longitude):
    latitude, longitude = float(latitude), float(longitude)
    _validate_singapore_location(latitude, longitude)
    radar_task = asyncio.create_task(get_radar_analysis(latitude, longitude))

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            endpoints = [details[0] for details in FEEDS.values()] + ["two-hr-forecast"]
            results = await asyncio.gather(
                *(_fetch_json(client, endpoint) for endpoint in endpoints),
                return_exceptions=True,
            )
    except httpx.HTTPError as error:
        raise WeatherUnavailableError("Could not reach the official weather service") from error

    observations = {}
    warnings = []
    for (name, (_, unit)), result in zip(FEEDS.items(), results[:-1]):
        if isinstance(result, Exception):
            warnings.append(f"{name} unavailable")
            observations[name] = None
            continue
        observation = _nearest_station_observation(
            result, latitude, longitude, result.get("readingUnit", unit)
        )
        if name == "wind_speed" and observation["unit"] == "knots":
            observation["value"] = round(observation["value"] * 1.852, 1)
            observation["unit"] = "km/h"
        observations[name] = observation
        if observation["is_stale"]:
            warnings.append(f"{name} reading is stale")

    forecast_result = results[-1]
    if isinstance(forecast_result, Exception):
        forecast = None
        warnings.append("two-hour forecast unavailable")
    else:
        forecast = _nearest_forecast(forecast_result, latitude, longitude)

    if observations["temperature"] is None:
        raise WeatherUnavailableError("A current temperature reading is required")

    try:
        radar = await radar_task
    except RadarUnavailableError:
        radar = None
        warnings.append("radar movement analysis unavailable")

    return {
        "location": {"latitude": latitude, "longitude": longitude},
        "observations": observations,
        "forecast": forecast,
        "radar": radar,
        "warnings": warnings,
        "source": "NEA via data.gov.sg",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_forecast_areas():
    """Return NEA's official two-hour forecast areas for manual selection."""
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            data = await _fetch_json(client, "two-hr-forecast")
    except httpx.HTTPError as error:
        raise WeatherUnavailableError("Could not load Singapore forecast areas") from error

    return sorted(
        [
            {
                "name": area["name"],
                "latitude": area["label_location"]["latitude"],
                "longitude": area["label_location"]["longitude"],
            }
            for area in data.get("area_metadata", [])
        ],
        key=lambda area: area["name"],
    )
