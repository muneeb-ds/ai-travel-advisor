from datetime import date

from pydantic import BaseModel, Field

from app.schemas.agent import Citation


# Geocoding Tool
class GeocodeInput(BaseModel):
    query: str = Field(..., description="The address or place name to geocode.")


class GeocodeOutput(BaseModel):
    latitude: float = Field(..., description="The latitude of the location.")
    longitude: float = Field(..., description="The longitude of the location.")
    display_name: str = Field(..., description="The display name of the location.")


# Weather Tool
class WeatherInput(BaseModel):
    latitude: float = Field(..., description="Latitude of the location.")
    longitude: float = Field(..., description="Longitude of the location.")
    start_date: date = Field(..., description="Start date for the forecast.")
    end_date: date = Field(..., description="End date for the forecast.")


class DailyWeather(BaseModel):
    forecast_date: date = Field(..., description="The date of the forecast.")
    max_temp: float = Field(..., description="Maximum temperature for the day.")
    min_temp: float = Field(..., description="Minimum temperature for the day.")
    weather_code: int = Field(..., description="WMO weather interpretation code.")


class WeatherOutput(BaseModel):
    daily: list[DailyWeather] = Field(..., description="The daily weather forecast.")


# Flights Tool
class FlightSearchInput(BaseModel):
    departure_airport: str = Field(..., description="Departure airport code (e.g., 'JFK').")
    arrival_airports: list[str] = Field(..., description="Arrival airport codes (e.g., 'LAX').")
    departure_date: date = Field(..., description="Departure date.")
    return_date: date | None = Field(None, description="Return date for round-trip flights.")
    max_results: int = Field(5, description="Maximum number of flight results to return.")


class FlightOption(BaseModel):
    airline: str = Field(..., description="Airline name.")
    flight_number: str = Field(..., description="Flight number.")
    departure_time: str = Field(..., description="Departure time.")
    arrival_time: str = Field(..., description="Arrival time.")
    price: float = Field(..., description="Price of the flight.")
    co2_emissions_kg: float = Field(..., description="Estimated CO₂ emissions in kilograms.")


class FlightSearchOutput(BaseModel):
    flights: list[FlightOption] = Field(..., description="List of available flight options.")


# Lodging Tool
class LodgingSearchInput(BaseModel):
    neighborhood: str = Field(..., description="Neighborhood to search for lodging.")
    start_date: date = Field(..., description="Check-in date.")
    end_date: date = Field(..., description="Check-out date.")
    min_price: float | None = Field(None, description="Minimum price per night.")
    max_price: float | None = Field(None, description="Maximum price per night.")
    family_amenities: bool = Field(
        False, description="Whether to filter for family-friendly amenities."
    )


class LodgingOption(BaseModel):
    name: str = Field(..., description="Name of the hotel or stay.")
    price_per_night: float = Field(..., description="Price per night.")
    cancellation_policy: str = Field(..., description="Cancellation policy.")
    distance_to_pois: dict[str, str] = Field(..., description="Distances to points of interest.")


class LodgingSearchOutput(BaseModel):
    lodging_options: list[LodgingOption] = Field(
        ..., description="List of available lodging options."
    )


# Events/Attractions Tool
class EventSearchInput(BaseModel):
    location: str = Field(..., description="Location to search for events (e.g., city name).")
    start_date: date = Field(..., description="Start date for events.")
    end_date: date = Field(..., description="End date for events.")
    kid_friendly: bool = Field(False, description="Whether to filter for kid-friendly events.")


class EventOption(BaseModel):
    name: str = Field(..., description="Name of the event or attraction.")
    opening_hours: str = Field(..., description="Opening hours.")
    kid_friendly: bool = Field(..., description="Whether the event is kid-friendly.")
    is_indoor: bool = Field(False, description="Whether the event is indoors.")


class EventSearchOutput(BaseModel):
    events: list[EventOption] = Field(..., description="List of available events and attractions.")


# Transit & Travel Time Tool
class TransitInput(BaseModel):
    origin: str = Field(..., description="Origin location.")
    destination: str = Field(..., description="Destination location.")


class TransitOutput(BaseModel):
    mode: str = Field(
        ..., description="Mode of transit (e.g., 'Train', 'Bus', 'Walk', 'Ride-Hail')."
    )
    travel_time: str = Field(..., description="Estimated travel time.")


# Currency Rates Tool
class CurrencyRatesInput(BaseModel):
    base_currency: str = Field("USD", description="The base currency for conversion rates.")
    target_currencies: list[str] = Field(..., description="List of target currency codes.")


class CurrencyRatesOutput(BaseModel):
    rates: dict[str, float] = Field(
        ..., description="Dictionary of currency codes to their rates against the base currency."
    )


# Knowledge Retrieval Tool
class KnowledgeRetrievalInput(BaseModel):
    query: str = Field(..., description="The query to search for in the knowledge base.")
    top_k: int = Field(5, description="The number of results to return.")


class KnowledgeRetrievalOutput(BaseModel):
    results: list[str] = Field(
        ..., description="List of relevant text chunks from the knowledge base."
    )
    citations: list[Citation] = Field(
        [], description="List of citations for the retrieved documents."
    )
