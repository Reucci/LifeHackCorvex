# Lightweight movement analysis for NEA's beta 70 km weather-radar feed

import asyncio
import math
import struct
import time
import zlib
from datetime import datetime, timedelta, timezone

import httpx


RADAR_URL = "https://api-open.data.gov.sg/v2/real-time/api/weather-radar-images/70km"
RADAR_CACHE_SECONDS = 240
MAX_SEARCH_DISTANCE_KM = 35

# Published NEA radar palette, ordered from light to heavy rainfall.
RADAR_COLOURS = [
    (0, 255, 255), (0, 239, 239), (0, 209, 213), (0, 186, 191),
    (0, 151, 154), (0, 131, 125), (0, 128, 69), (0, 137, 56),
    (0, 162, 53), (0, 183, 41), (0, 202, 17), (0, 218, 13),
    (0, 245, 7), (0, 255, 0), (67, 255, 65), (72, 255, 70),
    (255, 255, 59), (255, 255, 0), (255, 240, 0), (255, 220, 0),
    (255, 198, 0), (255, 178, 0), (255, 165, 0), (255, 138, 0),
    (255, 114, 0), (255, 73, 0), (255, 31, 0), (229, 0, 0),
    (193, 0, 0), (182, 0, 106), (210, 0, 165), (212, 0, 170),
    (255, 0, 255),
]

INTENSITY_BY_COLOUR = {
    colour: 1 if index <= 10 else 2 if index <= 15 else 3 if index <= 19 else 4 if index <= 24 else 5
    for index, colour in enumerate(RADAR_COLOURS)
}
INTENSITY_LABELS = {0: "none", 1: "light", 2: "light to moderate", 3: "moderate", 4: "moderate to heavy", 5: "heavy"}

_analysis_cache = {}


class RadarUnavailableError(RuntimeError):
    pass


def _paeth(left, above, upper_left):
    prediction = left + above - upper_left
    left_distance = abs(prediction - left)
    above_distance = abs(prediction - above)
    diagonal_distance = abs(prediction - upper_left)
    if left_distance <= above_distance and left_distance <= diagonal_distance:
        return left
    return above if above_distance <= diagonal_distance else upper_left


def decode_indexed_png(content):
    """Decode the non-interlaced, 8-bit indexed PNG format used by NEA."""
    if content[:8] != b"\x89PNG\r\n\x1a\n":
        raise RadarUnavailableError("Radar image is not a PNG")

    offset = 8
    palette = []
    transparency = []
    compressed = bytearray()
    width = height = None
    while offset < len(content):
        length = struct.unpack(">I", content[offset:offset + 4])[0]
        chunk_type = content[offset + 4:offset + 8]
        data = content[offset + 8:offset + 8 + length]
        offset += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, colour_type, _, _, interlace = struct.unpack(">IIBBBBB", data)
            if bit_depth != 8 or colour_type != 3 or interlace != 0:
                raise RadarUnavailableError("Unsupported radar PNG format")
        elif chunk_type == b"PLTE":
            palette = [tuple(data[index:index + 3]) for index in range(0, len(data), 3)]
        elif chunk_type == b"tRNS":
            transparency = list(data)
        elif chunk_type == b"IDAT":
            compressed.extend(data)
        elif chunk_type == b"IEND":
            break

    if not width or not palette:
        raise RadarUnavailableError("Radar PNG is incomplete")

    raw = zlib.decompress(bytes(compressed))
    rows = []
    position = 0
    previous = bytearray(width)
    for _ in range(height):
        filter_type = raw[position]
        position += 1
        scanline = bytearray(raw[position:position + width])
        position += width
        reconstructed = bytearray(width)
        for index, value in enumerate(scanline):
            left = reconstructed[index - 1] if index else 0
            above = previous[index]
            upper_left = previous[index - 1] if index else 0
            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = value + left
            elif filter_type == 2:
                result = value + above
            elif filter_type == 3:
                result = value + ((left + above) // 2)
            elif filter_type == 4:
                result = value + _paeth(left, above, upper_left)
            else:
                raise RadarUnavailableError("Unsupported PNG filter")
            reconstructed[index] = result & 255
        rows.append(reconstructed)
        previous = reconstructed

    strengths = []
    for row in rows:
        strengths.append([
            INTENSITY_BY_COLOUR.get(palette[index], 0)
            if index >= len(transparency) or transparency[index] > 0 else 0
            for index in row
        ])
    return width, height, strengths


def _target_pixel(boundary_box, latitude, longitude, width, height):
    upper_left = boundary_box["upperLeft"]
    lower_right = boundary_box["lowerRight"]
    x = (longitude - upper_left["longitude"]) / (lower_right["longitude"] - upper_left["longitude"]) * (width - 1)
    y = (upper_left["latitude"] - latitude) / (upper_left["latitude"] - lower_right["latitude"]) * (height - 1)
    return round(x), round(y)


def _analyse_frame(frame, boundary_box, latitude, longitude):
    width, height, strengths = decode_indexed_png(frame["content"])
    target_x, target_y = _target_pixel(boundary_box, latitude, longitude, width, height)
    degrees_width = boundary_box["lowerRight"]["longitude"] - boundary_box["upperLeft"]["longitude"]
    km_per_pixel = abs(degrees_width) * 111.0 * math.cos(math.radians(latitude)) / width
    search_pixels = max(1, round(MAX_SEARCH_DISTANCE_KM / km_per_pixel))
    local_pixels = max(1, round(3 / km_per_pixel))
    nearest = None
    local_strength = 0

    for y in range(max(0, target_y - search_pixels), min(height, target_y + search_pixels + 1)):
        for x in range(max(0, target_x - search_pixels), min(width, target_x + search_pixels + 1)):
            strength = strengths[y][x]
            if strength == 0:
                continue
            pixel_distance = math.hypot(x - target_x, y - target_y)
            if pixel_distance <= local_pixels:
                local_strength = max(local_strength, strength)
            if nearest is None or pixel_distance < nearest[0]:
                nearest = (pixel_distance, x, y, strength)

    if nearest:
        distance_pixels, rain_x, rain_y, strength = nearest
        nearest_distance = round(distance_pixels * km_per_pixel, 1)
        rain_longitude = boundary_box["upperLeft"]["longitude"] + rain_x / (width - 1) * degrees_width
        latitude_height = boundary_box["upperLeft"]["latitude"] - boundary_box["lowerRight"]["latitude"]
        rain_latitude = boundary_box["upperLeft"]["latitude"] - rain_y / (height - 1) * latitude_height
    else:
        nearest_distance = None
        rain_latitude = rain_longitude = None
        strength = 0

    return {
        "timestamp": frame["timestamp"],
        "nearest_rain_distance_km": nearest_distance,
        "nearest_rain_intensity": INTENSITY_LABELS[strength],
        "local_rain_intensity": INTENSITY_LABELS[local_strength],
        "nearest_rain_location": (
            {"latitude": round(rain_latitude, 4), "longitude": round(rain_longitude, 4)}
            if rain_latitude is not None else None
        ),
    }


def _movement_summary(frame_analyses):
    usable = [frame for frame in frame_analyses if frame["nearest_rain_distance_km"] is not None]
    latest = frame_analyses[-1]
    if not usable:
        return "no_nearby_rain", None, "high"
    if len(usable) < 2:
        return "insufficient_data", None, "low"

    oldest, newest = usable[0], usable[-1]
    elapsed_hours = (
        datetime.fromisoformat(newest["timestamp"]) - datetime.fromisoformat(oldest["timestamp"])
    ).total_seconds() / 3600
    if elapsed_hours <= 0:
        return "insufficient_data", None, "low"

    closure_kmh = (oldest["nearest_rain_distance_km"] - newest["nearest_rain_distance_km"]) / elapsed_hours
    if latest["local_rain_intensity"] != "none":
        return "overhead", 0, "high" if len(usable) >= 3 else "medium"
    if closure_kmh >= 5:
        eta = round(newest["nearest_rain_distance_km"] / closure_kmh * 60)
        return "approaching", max(5, min(120, eta)), "high" if len(usable) >= 3 else "medium"
    if closure_kmh <= -5:
        return "moving_away", None, "high" if len(usable) >= 3 else "medium"
    return "stationary", None, "medium" if len(usable) >= 3 else "low"


async def _radar_payload(client, date=None):
    response = await client.get(RADAR_URL, params={"date": date} if date else None)
    response.raise_for_status()
    payload = response.json()
    if payload.get("code") != 0 or not payload.get("data", {}).get("records"):
        raise RadarUnavailableError(payload.get("errorMsg") or "Radar data unavailable")
    return payload["data"]


async def get_radar_analysis(latitude, longitude):
    cache_key = (round(float(latitude), 3), round(float(longitude), 3))
    cached = _analysis_cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < RADAR_CACHE_SECONDS:
        return cached[1]

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            latest_payload = await _radar_payload(client)
            latest_record = latest_payload["records"][-1]
            latest_time = datetime.fromisoformat(latest_record["timestamp"])
            requested_times = [latest_time - timedelta(minutes=20), latest_time - timedelta(minutes=10)]
            older_payloads = await asyncio.gather(*(
                _radar_payload(client, moment.strftime("%Y-%m-%dT%H:%M:%S"))
                for moment in requested_times
            ))
            records = [payload["records"][-1] for payload in older_payloads] + [latest_record]
            unique_records = {record["timestamp"]: record for record in records}
            records = [unique_records[key] for key in sorted(unique_records)]
            image_responses = await asyncio.gather(*(client.get(record["image"]["url"]) for record in records))
            for response in image_responses:
                response.raise_for_status()
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise RadarUnavailableError("Could not retrieve recent radar frames") from error

    frames = [
        {"timestamp": record["timestamp"], "content": response.content}
        for record, response in zip(records, image_responses)
    ]
    analyses = [_analyse_frame(frame, latest_payload["boundaryBox"], latitude, longitude) for frame in frames]
    movement, eta_minutes, confidence = _movement_summary(analyses)
    latest = analyses[-1]
    radar_age = max(0, round((datetime.now(timezone.utc) - datetime.fromisoformat(latest["timestamp"])).total_seconds() / 60, 1))
    result = {
        "movement": movement,
        "eta_minutes": eta_minutes,
        "confidence": confidence,
        "local_rain_intensity": latest["local_rain_intensity"],
        "nearest_rain_distance_km": latest["nearest_rain_distance_km"],
        "nearest_rain_intensity": latest["nearest_rain_intensity"],
        "observed_at": latest["timestamp"],
        "age_minutes": radar_age,
        "frames_analysed": len(analyses),
        "frame_evidence": analyses,
        "method": "nearest-rain echo movement across georeferenced 70 km radar frames",
        "is_beta": True,
    }
    _analysis_cache[cache_key] = (time.monotonic(), result)
    return result
