# Multi-Hazard Agentic AI Emergency Response System

A new Python + LangGraph + Streamlit project. It takes an Indian city name, geocodes it, fetches live weather/forecast data, checks IMD/SACHET sources, runs deterministic hazard screening, and conditionally displays hazard-specific bulletins, precautions, emergency contacts and verified shelters.

## 1. Setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

If PowerShell blocks activation, use:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## 2. APIs

- Open-Meteo Geocoding: https://geocoding-api.open-meteo.com/v1/search
- Open-Meteo Forecast: https://api.open-meteo.com/v1/forecast
- IMD API reference: https://api.imd.gov.in/public/api_reference.html
- IMD official data access portal: https://api.imd.gov.in/public/index.php
- NDMA SACHET RSS feed directory: https://sachet.ndma.gov.in/CapFeed
- India emergency number: https://112.gov.in/

Open-Meteo is used for weather inputs and forecasts. It is not an official government warning source. IMD API endpoints may require account registration, access approval or an API token. Configure authorised credentials in `.env`; do not bypass access controls.

## 3. Important risk-engine design

The rules are deliberately transparent and conservative:
- IMD 24-hour rainfall bands: heavy 64.5–115.5 mm, very heavy 115.6–204.4 mm, extremely heavy >204.4 mm. Open-Meteo daily forecast precipitation is only an indicative forecast, not an IMD station observation.
- IMD plains heat-wave absolute maximum-temperature criteria include >=45°C and severe >=47°C; official declarations also depend on departure from normal, station type and duration.
- IMD plains cold-wave absolute minimum-temperature criteria include <=4°C and severe <=2°C; departure-from-normal and station-specific criteria also matter.
- IMD fog categories include moderate 200–500 m, dense 50–200 m and very dense <50 m. Visibility from a gridded API is not a substitute for a station observation.
- Thunderstorm WMO codes are indicators only. IMD district/station nowcast should be used for official thunderstorm severity.
- Cyclone risk must come from official IMD/RSMC cyclone bulletins and track information. Local wind speed alone must never create a cyclone prediction.
- Flood risk cannot be confirmed from rainfall alone. Production flood assessment needs CWC river levels/forecasts, antecedent rainfall, terrain, drainage and local exposure.
- UNKNOWN means missing/insufficient evidence; it must not be silently changed to LOW.

This prototype maps IMD warning colours into application labels: yellow -> MEDIUM; orange/red -> HIGH. Green/no warning can support LOW only when relevant data are available. This mapping is an application convention, not an official IMD three-level scale.

## 4. IMD API access

The code attempts the documented districtnowcast endpoint. If access returns 401/403 or an error, the app clearly records that IMD access is unavailable. Obtain credentials/access from the official IMD portal and set `IMD_API_TOKEN` in `.env` only if the API's documented authentication scheme matches Bearer tokens. If IMD issues a different scheme, update `services/imd_service.py` accordingly.


## 5. Add verified state/district contacts

Populate `data/emergency_contacts.csv` only after checking the official state/district government website:

`name,number,scope,state,district,source_url,verification_status`

The national 112 emergency number is included by default. Unverified state/district numbers are not fabricated.

## 6. Known limitations / production hardening

1. SACHET RSS matching in this starter version filters by city/state text and hazard keywords. It is not full CAP polygon intersection. Production should parse CAP XML and spatially intersect alert polygons with city coordinates.
2. IMD endpoint availability/authentication can change; verify endpoint schema and credentials with the official API portal.
3. Open-Meteo values are model/grid-based and may differ from local station observations.
4. The starter risk engine is a screening prototype, not an official forecast or evacuation order. Calibrate with IMD district/station bulletins and validate against historical events before public deployment.
5. Shelter data are intentionally empty until verified official records are supplied.
6. Use a state/district directory or authoritative government data to validate ambiguous city names and resolve district names correctly.
7. Add API caching, retries/backoff, monitoring, tests, and source freshness checks before production.

## 7. Official criteria reference links

- IMD API reference and nowcast category documentation: https://api.imd.gov.in/public/api_reference.html
- IMD definition/criteria poster: https://mausam.imd.gov.in/backend/assets/aiwfb_pdf/d7645ee338ad6a82de00e7ab953d376d.pdf
- SACHET RSS feed directory: https://sachet.ndma.gov.in/CapFeed
- NDMA SACHET portal: https://sachet.ndma.gov.in/
