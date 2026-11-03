import re
import requests
import feedparser
from config import SACHET_ALL_INDIA_RSS, REQUEST_TIMEOUT

HAZARD_TERMS = {
    "flood": ["flood", "inundation", "river level", "waterlogging", "dam release", "heavy rainfall"],
    "heatwave": ["heat wave", "heatwave", "hot day", "warm night"],
    "thunderstorm": ["thunderstorm", "lightning", "squall", "hailstorm"],
    "cyclone": ["cyclone", "depression", "deep depression", "storm surge", "tropical storm"],
    "cold_wave": ["cold wave", "coldwave", "cold day", "frost"],
    "dense_fog": ["dense fog", "very dense fog", "fog", "visibility"],
}

def _plain(text):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()

def fetch_sachet_bulletins(location: dict, hazards: list[str]) -> dict:
    response = requests.get(SACHET_ALL_INDIA_RSS, timeout=REQUEST_TIMEOUT,
                            headers={"User-Agent": "MultiHazardAI/1.0"})
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    city = (location.get("name") or "").casefold()
    state = (location.get("state") or "").casefold()
    matches = []
    for entry in feed.entries:
        title = _plain(entry.get("title", ""))
        summary = _plain(entry.get("summary", entry.get("description", "")))
        text = f"{title} {summary}".casefold()
        location_match = (city and city in text) or (state and state in text)
        # Do not show an unrelated national item merely because a hazard word matches.
        matched_hazards = [
            h for h in hazards
            if any(term in text for term in HAZARD_TERMS.get(h, [h.replace("_", " ")]))
        ]
        if location_match and (matched_hazards or not hazards):
            matches.append({
                "title": title,
                "summary": summary[:900],
                "published": entry.get("published", entry.get("updated", "Publication time not supplied")),
                "link": entry.get("link", "https://sachet.ndma.gov.in/"),
                "hazards": matched_hazards,
                "source": "NDMA SACHET RSS",
            })
    return {
        "source": "NDMA SACHET All-India RSS",
        "feed_url": SACHET_ALL_INDIA_RSS,
        "matches": matches,
        "checked_entries": len(feed.entries),
        "note": "RSS text matching is a discovery filter, not a geospatial CAP polygon intersection. Confirm the official alert and affected area before acting.",
    }
