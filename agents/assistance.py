from services.bulletin_service import fetch_sachet_bulletins
from services.imd_service import fetch_imd_district_nowcast, normalise_imd_nowcast
from pathlib import Path
import pandas as pd
from math import radians, sin, cos, asin, sqrt
from config import DATA_DIR

PRECAUTIONS = {
    "flood": [
        "Follow district administration and official evacuation instructions.",
        "Move to higher ground if flooding is occurring; do not walk or drive through floodwater.",
        "Keep drinking water, medicines, documents and a charged phone ready.",
        "Stay away from riverbanks, drains, underpasses and flowing water."
    ],
    "heatwave": [
        "Avoid strenuous outdoor activity during the hottest part of the day.",
        "Drink water regularly; use oral rehydration when advised by health authorities.",
        "Wear light, loose clothing and check on children, older adults and outdoor workers.",
        "Follow local health department advice; seek urgent medical help for heat illness."
    ],
    "thunderstorm": [
        "Move indoors or into a substantial enclosed building when thunder is heard.",
        "Stay away from isolated trees, rooftops, open fields, water and metal structures.",
        "Unplug sensitive electrical equipment where safe; avoid wired electrical appliances.",
        "Wait at least 30 minutes after the last thunder before resuming outdoor activity."
    ],
    "cyclone": [
        "Follow IMD and district administration warnings and evacuation orders.",
        "Move away from the coast and low-lying areas when instructed.",
        "Secure loose outdoor objects and keep an emergency kit ready.",
        "Do not go outdoors during the passage of the cyclone or enter floodwater."
    ],
    "cold_wave": [
        "Wear several layers and keep the head, neck, hands and feet covered.",
        "Limit prolonged exposure outdoors and check on vulnerable neighbours.",
        "Use heaters safely; never use charcoal or fuel-burning devices in enclosed rooms.",
        "Seek medical help for signs of hypothermia or frostbite."
    ],
    "dense_fog": [
        "Avoid unnecessary travel during dense fog.",
        "If driving is essential, slow down, use appropriate fog lights and maintain a large gap.",
        "Use lane markings and avoid high-beam headlights.",
        "Follow traffic police and transport authority advisories."
    ],
}

def get_precautions(hazards: list[str]) -> dict:
    return {h: PRECAUTIONS.get(h, []) for h in hazards if h in PRECAUTIONS}

def get_bulletins(location: dict, hazards: list[str]) -> dict:
    try:
        return fetch_sachet_bulletins(location, hazards)
    except Exception as exc:
        return {"source": "NDMA SACHET", "matches": [], "error": str(exc)}

def get_imd_nowcast(location: dict) -> dict:
    raw = fetch_imd_district_nowcast(location.get("district", ""))
    rows = normalise_imd_nowcast(raw, location.get("name", ""))
    return {"status": raw.get("available", False), "rows": rows, "source": raw.get("source"), "reason": raw.get("reason")}

def _distance_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2*r*asin(sqrt(a))

def find_verified_shelters(location: dict, hazards: list[str], limit: int = 3) -> list[dict]:
    path = DATA_DIR / "verified_shelters.csv"
    if not path.exists():
        return []
    df = pd.read_csv(path)
    required = {"shelter_name", "state", "district", "address", "latitude", "longitude", "hazard_types", "source_url", "verification_status"}
    if not required.issubset(df.columns):
        return []
    df = df[df["verification_status"].astype(str).str.lower().eq("verified")]
    df = df[df["state"].astype(str).str.casefold().eq(str(location.get("state", "")).casefold())]
    if hazards:
        keys = [h.replace("_", " ").casefold() for h in hazards]
        df = df[df["hazard_types"].astype(str).apply(lambda x: any(k in x.casefold() or "all" in x.casefold() for k in keys))]
    results = []
    for _, row in df.iterrows():
        try:
            lat, lon = float(row["latitude"]), float(row["longitude"])
            dist = _distance_km(float(location["latitude"]), float(location["longitude"]), lat, lon)
            results.append({
                "name": row["shelter_name"], "address": row["address"],
                "district": row["district"], "state": row["state"],
                "distance_km": round(dist, 2), "latitude": lat, "longitude": lon,
                "hazard_types": row["hazard_types"], "source_url": row["source_url"],
                "verification_date": row.get("verification_date", ""),
                "map_url": f"https://www.google.com/maps/dir/?api=1&origin={location['latitude']},{location['longitude']}&destination={lat},{lon}&travelmode=driving",
            })
        except (TypeError, ValueError):
            continue
    return sorted(results, key=lambda x: x["distance_km"])[:limit]

def get_emergency_contacts(location: dict) -> list[dict]:
    # Never invent district/state telephone numbers. Add only verified records to emergency_contacts.csv.
    contacts = [{"name": "National Emergency Response Support System", "number": "112",
                 "scope": "India", "source_url": "https://112.gov.in/"}]
    path = DATA_DIR / "emergency_contacts.csv"
    if path.exists():
        try:
            df = pd.read_csv(path).fillna("")
            for _, row in df.iterrows():
                if str(row.get("verification_status", "")).lower() != "verified":
                    continue
                if str(row.get("state", "")).casefold() not in ("all", str(location.get("state", "")).casefold()):
                    continue
                if str(row.get("district", "")).casefold() not in ("all", str(location.get("district", "")).casefold()):
                    continue
                contacts.append({"name": row.get("name"), "number": str(row.get("number")),
                                 "scope": row.get("scope"), "source_url": row.get("source_url")})
        except Exception:
            pass
    return contacts
