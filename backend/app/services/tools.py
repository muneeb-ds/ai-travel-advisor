import json
from datetime import date
from typing import Annotated

import httpx
from langchain.tools import tool
from langgraph.prebuilt.tool_node import InjectedState

from app.core.pgvector import get_embedding_pgvector_db_store
from app.schemas.agent import AgentState, Citation
from app.schemas.tools import (
    CurrencyRatesInput,
    CurrencyRatesOutput,
    DailyWeather,
    EventSearchInput,
    EventSearchOutput,
    FlightSearchInput,
    FlightSearchOutput,
    GeocodeInput,
    GeocodeOutput,
    KnowledgeRetrievalOutput,
    LodgingSearchInput,
    LodgingSearchOutput,
    TransitInput,
    TransitOutput,
    WeatherInput,
    WeatherOutput,
)

FLIGHTS_FIXTURE_PATH = "/app/app/fixtures/flights.json"
LODGING_FIXTURE_PATH = "/app/app/fixtures/lodging.json"
EVENTS_FIXTURE_PATH = "/app/app/fixtures/events.json"
CURRENCY_FIXTURE_PATH = "/app/app/fixtures/currency.json"


async def get_retriever(knowledge_item_ids: list[str] | None):
    vector_store = await get_embedding_pgvector_db_store()
    # To filter by multiple knowledge_item_id values, use a list for the value.
    # For example, to filter for ids "123", "456", and "789":
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5, "filter": {"knowledge_item_id": {"$in": knowledge_item_ids}}},
    )


# Fixture-based tools
@tool(args_schema=FlightSearchInput)
async def flights(
    departure_airport: str,
    arrival_airports: list[str],
    departure_date: date,
    return_date: date | None = None,
    max_results: int = 5,
) -> FlightSearchOutput:
    """Searches for flights based on departure and arrival airports.

    Args:
        departure_airport: The departure airport code.
        arrival_airports: The arrival airport codes.
        departure_date: The departure date.
        return_date: The return date (optional).
        max_results: The maximum number of results to return.

    Example:
        >>> flights(
        ...     departure_airport="SFO",
        ...     arrival_airports=["NRT", "HND"],
        ...     departure_date="2024-10-15",
        ...     return_date="2024-10-29",
        ... )
    """
    with open(FLIGHTS_FIXTURE_PATH) as f:
        flights = json.load(f)
    # Simple filtering logic for demonstration
    results = [f for f in flights if f["arrival_airport"] in arrival_airports]
    return FlightSearchOutput(flights=results[:max_results]).model_dump_json()


@tool(args_schema=LodgingSearchInput)
async def lodging(
    neighborhood: str,
    start_date: date,
    end_date: date,
    min_price: float | None = None,
    max_price: float | None = None,
    family_amenities: bool = False,
) -> LodgingSearchOutput:
    """Searches for lodging options in a specific neighborhood.

    Args:
        neighborhood: The neighborhood to search in.
        start_date: The check-in date.
        end_date: The check-out date.
        min_price: The minimum price per night (optional).
        max_price: The maximum price per night (optional).
        family_amenities: Whether to filter for family-friendly amenities.

    Example:
        >>> lodging(
        ...     neighborhood="Shibuya",
        ...     start_date="2024-10-15",
        ...     end_date="2024-10-29",
        ... )
    """
    with open(LODGING_FIXTURE_PATH) as f:
        lodging_options = json.load(f)
    # Simple filtering logic for demonstration
    results = [
        opt for opt in lodging_options if neighborhood.lower() in opt["neighborhood"].lower()
    ]
    return LodgingSearchOutput(lodging_options=results).model_dump_json()


@tool(args_schema=EventSearchInput)
async def events(
    location: str, start_date: date, end_date: date, kid_friendly: bool = False
) -> EventSearchOutput:
    """Searches for events in a specific location, with an option to filter for kid-friendly events.

    Args:
        location: The location to search for events.
        start_date: The start date for events.
        end_date: The end date for events.
        kid_friendly: Whether to filter for kid-friendly events.

    Example:
        >>> events(
        ...     location="Tokyo",
        ...     start_date="2024-10-15",
        ...     end_date="2024-10-29",
        ...     kid_friendly=True,
        ... )
    """
    with open(EVENTS_FIXTURE_PATH) as f:
        events = json.load(f)
    # Simple filtering logic for demonstration
    results = [
        e
        for e in events
        if location.lower() in e["location"].lower() and (not kid_friendly or e["kid_friendly"])
    ]
    return EventSearchOutput(events=results).model_dump_json()


@tool(args_schema=TransitInput)
async def transit(origin: str, destination: str) -> TransitOutput:
    """Provides transit information between two locations.

    Args:
        origin: The starting point.
        destination: The destination.

    Example:
        >>> transit(
        ...     origin="Shibuya Station",
        ...     destination="Tokyo Tower",
        ... )
    """
    # Fixture for demonstration
    return TransitOutput(
        mode="Train",
        travel_time="30 minutes",
    ).model_dump_json()


@tool(args_schema=CurrencyRatesInput)
async def currency_rates(
    target_currencies: list[str], base_currency: str = "USD"
) -> CurrencyRatesOutput:
    """Retrieves currency exchange rates for a given list of target currencies against a base currency.

    Args:
        target_currencies: A list of target currency codes.
        base_currency: The base currency for conversion rates (defaults to USD).

    Example:
        >>> currency_rates(target_currencies=["JPY", "EUR"])
    """
    # Fixture for demonstration
    with open(CURRENCY_FIXTURE_PATH) as f:
        currency_data = json.load(f)

    rates = {}
    for item in currency_data:
        if item["base_currency"] == base_currency:
            rates = item["rates"]
            break

    return CurrencyRatesOutput(
        rates={curr: rates.get(curr, 1.0) for curr in target_currencies}
    ).model_dump_json()


# API-based tools
@tool(args_schema=WeatherInput)
async def weather(
    latitude: float, longitude: float, start_date: date, end_date: date
) -> WeatherOutput:
    """Fetches daily weather forecasts for a given latitude and longitude between a start and end date.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        start_date: The start date for the forecast.
        end_date: The end date for the forecast.

    Example:
        >>> weather(
        ...     latitude=35.6895,
        ...     longitude=139.6917,
        ...     start_date="2024-10-15",
        ...     end_date="2024-10-29",
        ... )
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weathercode,temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )
        response.raise_for_status()
        data = response.json()

        # Transform data from API response to match our schema
        daily_forecasts = []
        if "daily" in data and "time" in data["daily"]:
            daily_data = data["daily"]
            for i, dt in enumerate(daily_data["time"]):
                daily_forecasts.append(
                    DailyWeather(
                        forecast_date=dt,
                        max_temp=daily_data["temperature_2m_max"][i],
                        min_temp=daily_data["temperature_2m_min"][i],
                        weather_code=daily_data["weathercode"][i],
                    )
                )

        return WeatherOutput(daily=daily_forecasts).model_dump_json()


@tool(args_schema=GeocodeInput)
async def geocoding(query: str) -> GeocodeOutput:
    """Converts a location query (like a city name or address) into geographic coordinates (latitude and longitude).

    Args:
        query: The location query.

    Example:
        >>> geocoding(query="Tokyo, Japan")
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 1},
        )
        response.raise_for_status()
        data = response.json()
        if not data:
            # Fallback to city center or raise error
            raise ValueError("Geocoding failed, no results found.")

        result = data[0]
        return GeocodeOutput(
            latitude=float(result["lat"]),
            longitude=float(result["lon"]),
            display_name=result["display_name"],
        ).model_dump_json()


@tool
async def knowledge_retrieval(query: str, state: Annotated[AgentState, InjectedState]) -> str:
    """Retrieves knowledge from the knowledge base.

    Args:
        query: The query to search for in the knowledge base.
        state: The current agent state, used to access knowledge base items.

    Example:
        >>> knowledge_retrieval(
        ...     query="What are some good restaurants in Shibuya?"
        ... )
    """
    retriever = await get_retriever(state["working_set"].knowledge_item_ids)

    docs = await retriever.ainvoke(query)

    if not docs:
        return KnowledgeRetrievalOutput(
            results=["I found no relevant information in the knowledge base"]
        ).model_dump_json()

    results = []
    citations = []
    for doc in docs:
        results.append(doc.page_content)
        metadata = doc.metadata or {}
        citations.append(
            Citation(
                title=metadata.get("title", "Untitled Document"),
                source=metadata.get("source", "knowledge_base"),
                ref=str(metadata.get("knowledge_item_id", "")),
            )
        )

    return KnowledgeRetrievalOutput(results=results, citations=citations).model_dump_json()
