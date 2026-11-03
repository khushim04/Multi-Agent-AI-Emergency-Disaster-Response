import requests
from config import IMD_API_BASE, IMD_API_TOKEN, REQUEST_TIMEOUT

def fetch_imd_district_nowcast(district: str = "") -> dict:
    # IMD documents district-wise nowcast at this endpoint. Access may require an authorised token.
    url = f"{IMD_API_BASE}/districtnowcast"
    params = {"id": district} if district else {}
    headers = {"Accept": "application/json"}
    if IMD_API_TOKEN:
        headers["Authorization"] = f"Bearer {IMD_API_TOKEN}"
    try:
        r = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code in (401, 403):
            return {"available": False, "reason": "IMD endpoint requires authorised access/credentials.", "source": url}
        r.raise_for_status()
        return {"available": True, "data": r.json(), "source": r.url}
    except requests.RequestException as exc:
        return {"available": False, "reason": str(exc), "source": url}

def normalise_imd_nowcast(raw: dict, city: str) -> list[dict]:
    if not raw.get("available"):
        return []
    data = raw.get("data", [])
    if isinstance(data, dict):
        data = data.get("data", data.get("result", []))
    if not isinstance(data, list):
        return []
    results = []
    for row in data:
        station = str(row.get("Station", row.get("station", "")))
        if city.casefold() in station.casefold() or not city:
            results.append({
                "station": station,
                "message": row.get("message", row.get("Message", "")),
                "color": row.get("color", row.get("Color")),
                "issued": row.get("toi", row.get("Date", "")),
                "valid_until": row.get("Vupto", ""),
                "raw": row,
            })
    return results
