
import streamlit as st
import html
from datetime import datetime
from zoneinfo import ZoneInfo

from graph_workflow import run_analysis


def format_ist_timestamp(timestamp):
    if not timestamp:
        return "Unavailable"

    try:
        dt = datetime.fromisoformat(
            timestamp.replace("Z", "+00:00")
        )

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC"))

        return dt.astimezone(
            ZoneInfo("Asia/Kolkata")
        ).strftime("%d %b %Y, %I:%M:%S %p IST")

    except (ValueError, TypeError):
        return timestamp


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Multi-Agent Emergency Response",
    page_icon="🌦️",
    layout="wide"
)

st.title("🚨 Multi-Agent Emergency Response for Disaster")

st.caption(
    "Real-time weather • IMD/SACHET bulletins • "
    "Explainable risk screening • Verified emergency resources"
)


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:

    st.header("City selection")

    city = st.text_input(
        "Enter an Indian city",
        placeholder="e.g. Bhopal, Patna, Chennai"
    )

    run = st.button(
        "Analyse city",
        type="primary",
        use_container_width=True
    )

    st.divider()

    st.caption(
        "Weather: Open-Meteo | Government alerts: IMD / NDMA SACHET"
    )

    st.caption(
        "Only shelters and local contacts with verified "
        "source records are displayed."
    )


# ==================================================
# RUN MULTI-AGENT WORKFLOW
# ==================================================

if run:

    if not city.strip():

        st.error("Please enter a city name.")

    else:

        with st.spinner(
            "Running location, weather, official-alert and risk agents..."
        ):

            try:

                result = run_analysis(city.strip())

                st.session_state["analysis_result"] = result

            except Exception as exc:

                st.error(f"Analysis failed: {exc}")

                st.info(
                    "Check your internet connection and API availability. "
                    "See README troubleshooting."
                )


# ==================================================
# DISPLAY RESULTS
# ==================================================

result = st.session_state.get("analysis_result")


if result:

    loc = result["location"]
    weather = result["weather"]
    current = weather.get("current", {})
    risk = result["risk"]


    # ==================================================
    # LOCATION
    # ==================================================

    st.subheader(
        f"📍 {loc['name']}, "
        f"{loc.get('state') or 'State not resolved'}, India"
    )

    st.caption(
        f"Coordinates: {loc['latitude']:.4f}, "
        f"{loc['longitude']:.4f} | "
        f"Timezone: {loc.get('timezone')}"
    )


    # ==================================================
    # LIVE WEATHER
    # ==================================================

    st.markdown("### 🌤️ Live weather")

    st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: clamp(19px, 2vw, 28px);
        white-space: nowrap;
    }
    </style>
    """, unsafe_allow_html=True)

    cols = st.columns(5)

    metrics = [
        ("Temperature", current.get("temperature_2m"), "°C"),
        ("Humidity", current.get("relative_humidity_2m"), "%"),
        ("Precipitation", current.get("precipitation"), " mm"),
        ("Wind speed", current.get("wind_speed_10m"), " km/h"),
        ("Wind gust", current.get("wind_gusts_10m"), " km/h"),
    ]

    for col, (label, value, suffix) in zip(cols, metrics):
        col.metric(
            label,
            "Unavailable" if value is None else f"{value}{suffix}"
        )

    st.caption(
        f"Weather source: {weather['source']} | "
        f"Observation time: "
        f"{format_ist_timestamp(weather.get('fetched_at_utc'))}"
    )


    # ==================================================
    # RISK ASSESSMENT
    # ==================================================

    st.markdown("### ⚠️ Risk assessment")

    overall = risk.get("overall_risk", "UNKNOWN")

    st.metric("Overall screening level", overall)

    st.warning(risk.get("important_note", ""))

    for item in risk.get("hazards", []):

        with st.expander(
            f"{item['hazard']} — {item['risk_level']}",
            expanded=item["risk_level"] in ("MEDIUM", "HIGH")
        ):

            for evidence in item.get("evidence", []):

                st.write("•", evidence)

            if item.get("official_warning_override"):

                st.write(
                    "Official warning override:",
                    item["official_warning_override"]
                )

            if item.get("limitation"):

                st.caption(item["limitation"])


    # ==================================================
    # GOVERNMENT BULLETINS
    # ==================================================

    st.markdown("### 📢 Government bulletins for detected hazards")

    bulletins = result.get("bulletins", {})

    if bulletins.get("error"):

        st.warning(
            f"SACHET feed could not be retrieved: {bulletins['error']}"
        )

    elif bulletins.get("matches"):

        for item in bulletins["matches"]:

            st.markdown(
                f"**[{item['title']}]({item['link']})**"
            )

            st.write(item.get("summary", ""))

            st.caption(
                f"{item.get('published')} | "
                f"{item.get('source')} | "
                f"Hazards: {', '.join(item.get('hazards', []))}"
            )

    else:

        st.info(
            "No city/state-and-hazard-matched SACHET RSS bulletin "
            "was found. This does not prove that no official warning "
            "exists. Check the linked official portals."
        )

    st.caption(
        f"Feed checked: {bulletins.get('feed_url', 'SACHET')}"
    )


    # ==================================================
    # SAFETY PRECAUTIONS - HOVER CARDS
    # ==================================================

    st.markdown("### 🛡️ Safety Precautions")

    st.caption(
        "Hover over a hazard card to reveal its recommended "
        "safety instructions."
    )

    precautions = result.get("precautions", {})

    if precautions:

        hazard_styles = {

            "flood": ("🌊", "#168BC5"),
            "thunderstorm": ("⛈️", "#9564D8"),
            "cyclone": ("🌀", "#E18A35"),
            "heatwave": ("🌡️", "#D95745"),
            "cold_wave": ("❄️", "#399ACB"),
            "dense_fog": ("🌫️", "#8496A8"),

        }


        # CSS DESIGN

        st.markdown(
            """
            <style>

            .precaution-grid {

                display: grid;

                grid-template-columns:
                    repeat(auto-fit, minmax(240px, 1fr));

                gap: 18px;

                margin-top: 15px;

                margin-bottom: 25px;

            }

            .precaution-card {

                background: linear-gradient(
                    145deg,
                    #172638,
                    #101923
                );

                border: 1px solid #34465A;

                border-radius: 14px;

                padding: 20px;

                min-height: 115px;

                transition: all 0.3s ease;

                cursor: pointer;

                overflow: hidden;

            }

            .precaution-card:hover,
            .precaution-card:focus-within {

                border-color: #45B7D1;

                transform: translateY(-4px);

                box-shadow:
                    0 8px 24px rgba(0, 0, 0, 0.35);

            }

            .precaution-heading {

                display: flex;

                align-items: center;

                gap: 13px;

                font-size: 19px;

                font-weight: 700;

                color: #F1F5F9;

            }

            .precaution-icon {

                font-size: 30px;

            }

            .hover-hint {

                color: #9BAFC2;

                font-size: 12px;

                margin-top: 12px;

            }

            .precaution-details {

                max-height: 0;

                opacity: 0;

                overflow: hidden;

                transition:
                    max-height 0.45s ease,
                    opacity 0.35s ease,
                    margin 0.35s ease;

                margin-top: 0;

            }

            .precaution-card:hover .precaution-details,
            .precaution-card:focus-within .precaution-details {

                max-height: 800px;

                opacity: 1;

                margin-top: 17px;

            }

            .precaution-details ul {

                padding-left: 20px;

                margin-bottom: 0;

            }

            .precaution-details li {

                color: #D5E0EB;

                font-size: 14px;

                line-height: 1.65;

                margin-bottom: 10px;

            }

            </style>
            """,
            unsafe_allow_html=True
        )


        # CREATE HTML CARDS

        cards = []

        for hazard, items in precautions.items():

            key = hazard.lower().replace(" ", "_")

            icon, accent = hazard_styles.get(
                key,
                ("⚠️", "#45B7D1")
            )

            title = html.escape(
                hazard.replace("_", " ").title()
            )

            points = "".join(
                f"<li>{html.escape(str(item))}</li>"
                for item in items
            )

            card = f"""
            <div class="precaution-card"
                 tabindex="0"
                 style="border-top: 3px solid {accent};">

                <div class="precaution-heading">

                    <span class="precaution-icon">{icon}</span>

                    <span>{title}</span>

                </div>

                <div class="hover-hint">
                    ↗ Hover to view safety precautions
                </div>

                <div class="precaution-details">

                    <ul>
                        {points}
                    </ul>

                </div>

            </div>
            """

            cards.append(card)


        # IMPORTANT: st.html RENDERS HTML DIRECTLY

        html_content = (
            '<div class="precaution-grid">'
            + "".join(cards)
            + '</div>'
        )

        st.html(html_content)

    else:

        st.success(
            "No MEDIUM/HIGH screening hazard was detected "
            "from the available inputs. Continue monitoring "
            "official bulletins."
        )


    # ==================================================
    # EMERGENCY CONTACTS
    # ==================================================

    st.markdown("### 📞 Emergency contacts")

    for contact in result.get("contacts", []):

        st.write(
            f"**{contact['name']} — {contact['number']}** "
            f"({contact['scope']})"
        )

        st.caption(contact.get("source_url", ""))


    # ==================================================
    # VERIFIED GOVERNMENT SHELTERS
    # ==================================================

    st.markdown("### 📍 Verified government shelters")

    shelters = result.get("shelters", [])

    if shelters:

        for shelter in shelters:

            st.markdown(
                f"**{shelter['name']}** — "
                f"{shelter['distance_km']} km"
            )

            st.write(
                shelter["address"],
                shelter["district"],
                shelter["state"]
            )

            st.markdown(
                f"[Official source]({shelter['source_url']}) · "
                f"[Google Maps directions]({shelter['map_url']})"
            )

            st.caption(
                f"Verification date: "
                f"{shelter.get('verification_date', 'Not supplied')}"
            )

    else:

        st.info(
            "No matching verified shelter record is currently "
            "available in data/verified_shelters.csv. "
            "The system intentionally does not invent shelter "
            "names or locations."
        )


    # ==================================================
    # DATA SOURCES AND LIMITATIONS
    # ==================================================

    st.markdown("### 📚 Data sources and limitations")

    st.write(
        "- IMD district nowcast:",
        result.get(
            "imd", {}
        ).get(
            "reason",
            "Check availability status in IMD source response."
        )
    )

    st.write(
        "- Weather is from Open-Meteo and is not itself "
        "an official IMD warning."
    )

    st.write(
        "- The current prototype's SACHET matching uses "
        "city/state text in RSS entries; full CAP polygon "
        "geospatial matching is a future enhancement."
    )

    st.write(
        "- This is a prototype decision-support tool, not "
        "an official warning, evacuation instruction or "
        "substitute for local authorities."
    )


else:

    st.info(
        "Enter an Indian city in the sidebar and select "
        "Analyse city to start the multi-agent workflow."
    )
