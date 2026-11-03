from datetime import datetime
from typing import Any

def _values(weather: dict):
    c = weather.get("current", {})
    d = weather.get("daily", {})
    h = weather.get("hourly", {})
    def first(arr):
        return arr[0] if isinstance(arr, list) and arr else None
    return c, d, h, first

def _official_level(alerts: list[dict], hazard: str):
    # IMD warning colours: yellow=watch, orange=alert, red=warning.
    levels = []
    for a in alerts:
        text = (a.get("message", "") + " " + str(a.get("raw", {}))).casefold()
        if hazard.replace("_", " ") in text or any(
            term in text for term in {
                "flood": ["heavy rain", "very heavy rain", "extremely heavy rain", "flood"],
                "heatwave": ["heat wave", "heatwave", "hot day"],
                "thunderstorm": ["thunderstorm", "lightning", "squall"],
                "cyclone": ["cyclone", "depression"],
                "cold_wave": ["cold wave", "coldwave"],
                "dense_fog": ["fog", "visibility"],
            }[hazard]
        ):
            color = str(a.get("color", "")).casefold()
            if color in ("4", "red"):
                levels.append("HIGH")
            elif color in ("3", "orange"):
                levels.append("HIGH")
            elif color in ("2", "yellow"):
                levels.append("MEDIUM")
    return "HIGH" if "HIGH" in levels else ("MEDIUM" if levels else None)

def assess_hazards(weather: dict, imd_nowcasts: list[dict], sachet_matches: list[dict]) -> dict:
    c, d, h, first = _values(weather)
    temp = c.get("temperature_2m")
    humidity = c.get("relative_humidity_2m")
    wind = c.get("wind_speed_10m")
    gust = c.get("wind_gusts_10m")
    visibility = c.get("visibility")
    precip_now = c.get("precipitation")
    daily_rain = d.get("precipitation_sum", [])
    max_temp = first(d.get("temperature_2m_max", []))
    min_temp = first(d.get("temperature_2m_min", []))
    max_rain = max([x for x in daily_rain if isinstance(x, (int, float))], default=None)
    wmo_codes = h.get("weather_code", [])
    has_thunder_code = any(code in (95, 96, 99) for code in wmo_codes if isinstance(code, (int, float)))

    results = []
    def add(name, level, evidence, limitation=None):
        official = _official_level(imd_nowcasts, name)
        # Official alert takes precedence; do not downgrade.
        if official == "HIGH":
            level = "HIGH"
        elif official == "MEDIUM" and level == "LOW":
            level = "MEDIUM"
        results.append({
            "hazard": name.replace("_", " ").title(),
            "key": name,
            "risk_level": level,
            "evidence": evidence,
            "official_warning_override": official,
            "limitation": limitation,
        })

    # Rainfall categories are IMD's 24-hour station rainfall categories.
    # Open-Meteo forecast precipitation is indicative, not a substitute for IMD gauge observation.
    if max_rain is None:
        rain_level = "UNKNOWN"
        rain_evidence = ["Daily precipitation forecast unavailable."]
    elif max_rain >= 115.6:
        rain_level = "HIGH"
        rain_evidence = [f"Forecast daily precipitation peak: {max_rain:.1f} mm; exceeds IMD very-heavy-rain threshold (115.6 mm/24h)."]
    elif max_rain >= 64.5:
        rain_level = "MEDIUM"
        rain_evidence = [f"Forecast daily precipitation peak: {max_rain:.1f} mm; within IMD heavy-rain band (64.5–115.5 mm/24h)."]
    else:
        rain_level = "LOW"
        rain_evidence = [f"Forecast daily precipitation peak: {max_rain:.1f} mm; below IMD heavy-rain threshold."]
    add("flood", rain_level, rain_evidence,
        "Rainfall alone cannot establish flood risk. A proper flood assessment needs river gauge/CWC alerts, antecedent rainfall, terrain, drainage and local exposure.")

    # IMD heatwave requires station type, persistence and/or departure from normal.
    if max_temp is None:
        level, ev = "UNKNOWN", ["Daily maximum temperature forecast unavailable."]
    elif max_temp >= 47:
        level, ev = "HIGH", [f"Forecast maximum {max_temp:.1f}°C reaches IMD severe heat-wave absolute-temperature threshold (>=47°C for plains)."]
    elif max_temp >= 45:
        level, ev = "MEDIUM", [f"Forecast maximum {max_temp:.1f}°C reaches IMD heat-wave absolute-temperature threshold (>=45°C for plains)."]
    else:
        level, ev = "LOW", [f"Forecast maximum {max_temp:.1f}°C is below IMD plains absolute-temperature heat-wave threshold; departure-from-normal criteria still require station normals."]
    add("heatwave", level, ev, "Final IMD heat-wave declaration depends on station geography, climatological departure and duration criteria. This is a screening estimate.")

    # Thunderstorm: Open-Meteo WMO code is an indicator only; IMD nowcast is preferred.
    if has_thunder_code:
        level, ev = "MEDIUM", ["Hourly forecast includes a thunderstorm WMO weather code."]
    elif gust is not None and gust >= 62:
        level, ev = "MEDIUM", [f"Current gust {gust:.1f} km/h; high-wind conditions warrant checking IMD nowcast."]
    elif gust is not None:
        level, ev = "LOW", [f"Current gust {gust:.1f} km/h; no thunderstorm WMO code in available hourly forecast."]
    else:
        level, ev = "UNKNOWN", ["Thunderstorm indicators unavailable."]
    add("thunderstorm", level, ev, "Thunderstorm/lightning severity should be taken from IMD nowcast; CAPE or a weather code alone does not prove a thunderstorm warning.")

    # Cyclone must be bulletin-driven, never inferred from local wind speed alone.
    cyclone_alert = any("cyclone" in (b.get("title", "") + " " + b.get("summary", "")).casefold()
                        for b in sachet_matches)
    add("cyclone", "MEDIUM" if cyclone_alert else "UNKNOWN",
        ["A location-matched cyclone bulletin was found." if cyclone_alert else "No cyclone bulletin matched this city in the retrieved SACHET feed."],
        "Cyclone classification requires official IMD/RSMC cyclone bulletins, track, wind category, forecast cone and coastal impact. No bulletin match is not proof of no cyclone risk.")

    # Cold wave absolute thresholds apply to plains; normal departure unavailable in standard weather API.
    if min_temp is None:
        level, ev = "UNKNOWN", ["Daily minimum temperature forecast unavailable."]
    elif min_temp <= 2:
        level, ev = "HIGH", [f"Forecast minimum {min_temp:.1f}°C reaches IMD severe cold-wave absolute threshold for plains (<=2°C)."]
    elif min_temp <= 4:
        level, ev = "MEDIUM", [f"Forecast minimum {min_temp:.1f}°C reaches IMD cold-wave absolute threshold for plains (<=4°C)."]
    else:
        level, ev = "LOW", [f"Forecast minimum {min_temp:.1f}°C is above IMD plains absolute cold-wave threshold; departure-from-normal criteria still require station normals."]
    add("cold_wave", level, ev, "Apply only the appropriate plains/coastal/hill-station criteria and check minimum-temperature departure from normal.")

    # IMD fog categories: dense 50–200m; very dense <50m. API visibility is in metres.
    if visibility is None:
        level, ev = "UNKNOWN", ["Current visibility unavailable."]
    elif visibility < 50:
        level, ev = "HIGH", [f"Current visibility {visibility:.0f} m; below IMD very-dense-fog threshold (<50 m)."]
    elif visibility <= 200:
        level, ev = "HIGH", [f"Current visibility {visibility:.0f} m; within IMD dense-fog band (50–200 m)."]
    elif visibility <= 500:
        level, ev = "MEDIUM", [f"Current visibility {visibility:.0f} m; within IMD moderate-fog band (200–500 m)."]
    elif visibility < 1000:
        level, ev = "LOW", [f"Current visibility {visibility:.0f} m; fog present (<1 km), but not dense by the IMD threshold."]
    else:
        level, ev = "LOW", [f"Current visibility {visibility:.0f} m; above the IMD fog threshold."]
    add("dense_fog", level, ev, "Visibility from a gridded forecast API may differ from a local IMD station observation.")

    known = [x for x in results if x["risk_level"] in ("LOW", "MEDIUM", "HIGH")]
    overall = "UNKNOWN"
    if known:
        overall = "HIGH" if any(x["risk_level"] == "HIGH" for x in known) else (
            "MEDIUM" if any(x["risk_level"] == "MEDIUM" for x in known) else "LOW")
    active = [x for x in results if x["risk_level"] in ("MEDIUM", "HIGH")]
    return {
        "overall_risk": overall,
        "hazards": results,
        "active_hazards": [x["key"] for x in active],
        "method": "Deterministic screening rules grounded in published IMD criteria; official warning data takes precedence when available.",
        "important_note": "This prototype is decision support, not an official forecast or evacuation order. UNKNOWN means insufficient evidence, not LOW risk.",
    }
