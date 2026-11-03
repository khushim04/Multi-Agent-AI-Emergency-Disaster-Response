from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

OPEN_METEO_GEOCODING = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
SACHET_ALL_INDIA_RSS = "https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml"
SACHET_FEED_PAGE = "https://sachet.ndma.gov.in/CapFeed"
IMD_API_BASE = os.getenv("IMD_API_BASE", "https://api.imd.gov.in/api/v1").rstrip("/")
IMD_API_TOKEN = os.getenv("IMD_API_TOKEN", "").strip()
OSRM_BASE = os.getenv("OSRM_BASE", "https://router.project-osrm.org").rstrip("/")
REQUEST_TIMEOUT = 25
