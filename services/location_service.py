import requests
from config import OPEN_METEO_GEOCODING, REQUEST_TIMEOUT

def geocode_indian_city(city: str) -> dict:
    if not city or not city.strip():
        raise ValueError("Enter an Indian city name.")
    params = {"name": city.strip(), "count": 10, "language": "en", "format": "json", "countryCode": "IN"}
    response = requests.get(OPEN_METEO_GEOCODING, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    results = response.json().get("results", [])
    if not results:
        raise ValueError(f"No Indian location found for '{city}'. Check the spelling.")
    # Prefer exact city-name match, then populated settlements.
    wanted = city.strip().casefold()
    results.sort(key=lambda x: (
        x.get("name", "").casefold() != wanted,
        x.get("feature_code", "") not in ("PPL", "PPLA", "PPLA2", "PPLA3", "PPLC"),
    ))
    place = results[0]
    return {
        "name": place.get("name"),
        "admin1": place.get("admin1", ""),
        "admin2": place.get("admin2", ""),
        "state": place.get("admin1", ""),
        "district": place.get("admin2", ""),
        "country": place.get("country", "India"),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": place.get("timezone", "Asia/Kolkata"),
        "feature_code": place.get("feature_code"),
        "geocoding_source": "Open-Meteo Geocoding API",
    }
