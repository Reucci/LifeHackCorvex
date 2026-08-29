import httpx

# data.gov.sg's real-time environment APIs — public, no API key required.
BASE_URL = "https://api.data.gov.sg/v1/environment"
FORECAST_URL = f"{BASE_URL}/2-hour-weather-forecast"
TEMPERATURE_URL = f"{BASE_URL}/air-temperature"
HUMIDITY_URL = f"{BASE_URL}/relative-humidity"
WIND_SPEED_URL = f"{BASE_URL}/wind-speed"

# No single "nearest station" without user geolocation, so island-wide
# readings are averaged; the 2-hour forecast text for a central area
# ("City") stands in for the general condition/icon/rain flag.
REPRESENTATIVE_AREA = "City"
KNOTS_TO_KMH = 1.852

RAIN_KEYWORDS = ("rain", "shower", "thundery")

ICON_KEYWORDS = (
    ("thundery", "⛈️"),
    ("rain", "🌧️"),
    ("shower", "🌧️"),
    ("mist", "🌫️"),
    ("fog", "🌫️"),
    ("haze", "🌫️"),
    ("cloudy", "☁️"),
    ("overcast", "☁️"),
    ("windy", "🌬️"),
    ("fair", "☀️"),
    ("sunny", "☀️"),
    ("clear", "☀️"),
)


def _average_reading(url: str) -> float:
    response = httpx.get(url, timeout=8.0)
    response.raise_for_status()
    readings = response.json()["items"][0]["readings"]
    values = [r["value"] for r in readings]
    return sum(values) / len(values)


def _forecast_condition(area: str = REPRESENTATIVE_AREA) -> str:
    response = httpx.get(FORECAST_URL, timeout=8.0)
    response.raise_for_status()
    forecasts = response.json()["items"][0]["forecasts"]
    match = next((f for f in forecasts if f["area"] == area), forecasts[0])
    return match["forecast"]


def _icon_for(condition: str) -> str:
    lowered = condition.lower()
    for keyword, icon in ICON_KEYWORDS:
        if keyword in lowered:
            return icon
    return "🌤️"


def get_weather_snapshot() -> dict:
    condition = _forecast_condition()
    temp = _average_reading(TEMPERATURE_URL)
    humidity = _average_reading(HUMIDITY_URL)
    wind_speed_knots = _average_reading(WIND_SPEED_URL)

    lowered_condition = condition.lower()
    is_raining = any(keyword in lowered_condition for keyword in RAIN_KEYWORDS)

    return {
        "temp": round(temp, 1),
        "humidity": round(humidity),
        "windSpeed": round(wind_speed_knots * KNOTS_TO_KMH, 1),
        "isRaining": is_raining,
        "icon": _icon_for(condition),
        "place": "Singapore",
    }
