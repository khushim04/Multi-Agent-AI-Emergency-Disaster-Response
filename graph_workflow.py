from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from services.location_service import geocode_indian_city
from services.weather_service import fetch_live_weather
from risk_engine.rules import assess_hazards
from agents.assistance import (
    get_bulletins, get_precautions, get_emergency_contacts,
    find_verified_shelters, get_imd_nowcast
)

ALL_HAZARDS = ["flood", "heatwave", "thunderstorm", "cyclone", "cold_wave", "dense_fog"]

class EmergencyState(TypedDict, total=False):
    city_query: str
    location: dict
    weather: dict
    imd: dict
    risk: dict
    bulletins: dict
    precautions: dict
    contacts: list
    shelters: list
    error: str

def location_node(state: EmergencyState):
    return {"location": geocode_indian_city(state["city_query"])}

def weather_node(state: EmergencyState):
    return {"weather": fetch_live_weather(state["location"])}

def imd_node(state: EmergencyState):
    return {"imd": get_imd_nowcast(state["location"])}

def initial_bulletin_node(state: EmergencyState):
    # Fetch city/state bulletin candidates for all supported hazards before final risk routing.
    return {"bulletins": get_bulletins(state["location"], ALL_HAZARDS)}

def risk_node(state: EmergencyState):
    imd_rows = state.get("imd", {}).get("rows", [])
    sachet = state.get("bulletins", {}).get("matches", [])
    return {"risk": assess_hazards(state["weather"], imd_rows, sachet)}

def filter_bulletins_node(state: EmergencyState):
    active = set(state.get("risk", {}).get("active_hazards", []))
    bulletin_data = dict(state.get("bulletins", {}))
    bulletin_data["matches"] = [
        item for item in bulletin_data.get("matches", [])
        if active.intersection(item.get("hazards", []))
    ]
    return {"bulletins": bulletin_data}

def risk_route(state: EmergencyState):
    return "assistance" if state.get("risk", {}).get("active_hazards") else "normal"

def assistance_node(state: EmergencyState):
    active = state.get("risk", {}).get("active_hazards", [])
    return {
        "precautions": get_precautions(active),
        "contacts": get_emergency_contacts(state["location"]),
        "shelters": find_verified_shelters(state["location"], active),
    }

def normal_node(state: EmergencyState):
    return {
        "precautions": {},
        "contacts": get_emergency_contacts(state["location"]),
        "shelters": [],
    }

def build_graph():
    graph = StateGraph(EmergencyState)
    graph.add_node("location", location_node)
    graph.add_node("weather", weather_node)
    graph.add_node("imd", imd_node)
    graph.add_node("bulletins", initial_bulletin_node)
    graph.add_node("risk", risk_node)
    graph.add_node("filter_bulletins", filter_bulletins_node)
    graph.add_node("assistance", assistance_node)
    graph.add_node("normal", normal_node)
    graph.add_edge(START, "location")
    graph.add_edge("location", "weather")
    graph.add_edge("weather", "imd")
    graph.add_edge("imd", "bulletins")
    graph.add_edge("bulletins", "risk")
    graph.add_edge("risk", "filter_bulletins")
    graph.add_conditional_edges("filter_bulletins", risk_route, {"assistance": "assistance", "normal": "normal"})
    graph.add_edge("assistance", END)
    graph.add_edge("normal", END)
    return graph.compile()

def run_analysis(city: str) -> dict:
    return build_graph().invoke({"city_query": city})
