import requests
from config import OPEN_METEO_FORECAST, REQUEST_TIMEOUT

def fetch_live_weather(location: dict) -> dict:
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": [
            "temperature_2m", "relative_humidity_2m", "precipitation", "rain",
            "showers", "snowfall", "weather_code", "wind_speed_10m",
            "wind_gusts_10m", "wind_direction_10m", "surface_pressure",
            "visibility"
        ],
        "hourly": [
            "temperature_2m", "relative_humidity_2m", "precipitation",
            "precipitation_probability", "wind_speed_10m", "wind_gusts_10m",
            "visibility", "cape", "weather_code"
        ],
        "daily": [
            "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
            "rain_sum", "wind_speed_10m_max", "wind_gusts_10m_max",
            "weather_code"
        ],
        "forecast_days": 3,
        "past_days": 1,
        "timezone": location.get("timezone", "Asia/Kolkata"),
    }
    response = requests.get(OPEN_METEO_FORECAST, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    return {
        "source": "Open-Meteo Forecast API",
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "timezone": payload.get("timezone"),
        "current": payload.get("current", {}),
        "hourly": payload.get("hourly", {}),
        "daily": payload.get("daily", {}),
        "fetched_at_utc": payload.get("current", {}).get("time"),
        "units": {
            "current": payload.get("current_units", {}),
            "hourly": payload.get("hourly_units", {}),
            "daily": payload.get("daily_units", {}),
        },
        "note": "Open-Meteo is a weather data provider, not an Indian government warning authority. Official warnings are checked separately.",
    }
