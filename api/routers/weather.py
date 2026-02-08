"""
Weather API Routes
RESTful endpoints for weather data retrieval and analytics
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from api.services.weather_service import get_weather_service, WeatherUnits

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/weather",
    tags=["weather"]
)

# Request/Response Models

class LocationRequest(BaseModel):
    """Request model for weather by location"""
    city: str = Field(..., description="City name")
    country_code: str = Field("IN", description="ISO 3166 country code")


class CoordinatesRequest(BaseModel):
    """Request model for weather by coordinates"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class WeatherResponse(BaseModel):
    """Current weather response"""
    location: str
    latitude: float
    longitude: float
    timestamp: datetime
    temperature: float
    feels_like: float
    temp_min: float
    temp_max: float
    humidity: int
    condition: str
    description: str
    wind_speed: float
    pressure: int
    rainfall_1h: float
    visibility: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Mumbai, IN",
                "latitude": 19.076,
                "longitude": 72.8777,
                "timestamp": "2025-02-07T15:30:00",
                "temperature": 28.5,
                "feels_like": 30.0,
                "temp_min": 26.0,
                "temp_max": 32.0,
                "humidity": 65,
                "condition": "Partly Cloudy",
                "description": "partly cloudy",
                "wind_speed": 12.5,
                "pressure": 1012,
                "rainfall_1h": 0,
                "visibility": 10000,
            }
        }


class ForecastResponse(BaseModel):
    """Weather forecast response"""
    location: str
    latitude: float
    longitude: float
    forecast_count: int
    forecasts: List[dict]


class WeatherImpactResponse(BaseModel):
    """Weather impact analysis response"""
    location: str
    weather_condition: str
    temperature: float
    impact_score: float
    impact_description: str
    retail_impact: str


# API Endpoints

@router.get(
    "/current",
    response_model=WeatherResponse,
    summary="Get current weather",
    description="Fetch current weather data for a specific location"
)
async def get_current_weather(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code")
):
    """
    Get current weather for a location
    
    **Parameters:**
    - `city`: City name (e.g., 'Mumbai', 'Delhi')
    - `country_code`: ISO 3166 country code (default: 'IN' for India)
    
    **Returns:**
    Current weather data including temperature, humidity, wind speed, etc.
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather(city, country_code)
        
        if 'is_mock' in weather:
            logger.warning(f"Using mock data for {city}, {country_code}")
        
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching weather for {city}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/current/coordinates",
    response_model=WeatherResponse,
    summary="Get current weather by coordinates",
    description="Fetch current weather data by latitude/longitude"
)
async def get_current_weather_coordinates(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """
    Get current weather for coordinates
    
    **Parameters:**
    - `latitude`: Latitude (-90 to 90)
    - `longitude`: Longitude (-180 to 180)
    
    **Returns:**
    Current weather data for the specified coordinates
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather_by_coordinates(latitude, longitude)
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching weather for ({latitude}, {longitude}): {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="Get 5-day weather forecast",
    description="Fetch 5-day weather forecast for a location"
)
async def get_weather_forecast(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code"),
    days: int = Query(5, ge=1, le=5, description="Number of days (max 5)")
):
    """
    Get weather forecast for next N days
    
    **Parameters:**
    - `city`: City name
    - `country_code`: ISO 3166 country code
    - `days`: Number of forecast days (1-5, default: 5)
    
    **Returns:**
    Weather forecast data with 3-hour intervals
    """
    try:
        service = get_weather_service()
        forecast = service.get_forecast(city, country_code, days)
        return forecast
        
    except Exception as e:
        logger.error(f"Error fetching forecast for {city}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")


@router.post(
    "/multi-location",
    summary="Get weather for multiple retail locations",
    description="Fetch weather for multiple store locations in one request"
)
async def get_multi_location_weather(
    locations: List[LocationRequest]
):
    """
    Get weather for multiple locations
    
    **Request body:** List of location objects with city and country_code
    
    **Returns:**
    Dictionary mapping location strings to weather data
    
    **Example request:**
    ```json
    [
      {"city": "Mumbai", "country_code": "IN"},
      {"city": "Delhi", "country_code": "IN"},
      {"city": "Bangalore", "country_code": "IN"}
    ]
    ```
    """
    try:
        service = get_weather_service()
        location_tuples = [(loc.city, loc.country_code) for loc in locations]
        weather_data = service.get_weather_for_retail_locations(location_tuples)
        return weather_data
        
    except Exception as e:
        logger.error(f"Error fetching multi-location weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.post(
    "/impact-analysis",
    response_model=WeatherImpactResponse,
    summary="Analyze weather impact on retail",
    description="Calculate weather impact score for demand forecasting"
)
async def analyze_weather_impact(
    city: str = Query(..., description="City name"),
    country_code: str = Query("IN", description="ISO 3166 country code")
):
    """
    Analyze weather impact on retail demand
    
    **Parameters:**
    - `city`: City name
    - `country_code`: ISO 3166 country code
    
    **Returns:**
    Weather impact score (0.0-2.0) and interpretation for retail demand
    
    **Impact Scores:**
    - < 0.8: Negative impact (bad weather reduces foot traffic)
    - 0.8-1.2: Neutral/Positive impact
    - > 1.2: Strong positive impact
    """
    try:
        service = get_weather_service()
        weather = service.get_current_weather(city, country_code)
        
        impact_score = service.calculate_weather_impact(
            weather['condition'],
            weather['temperature']
        )
        
        # Generate description
        if impact_score < 0.8:
            description = "Negative impact - Consider lower stock expectations"
            retail_impact = "Reduced foot traffic expected"
        elif impact_score < 1.0:
            description = "Slightly negative - Minor impact on demand"
            retail_impact = "Slight reduction in customer visits"
        elif impact_score <= 1.1:
            description = "Neutral - Normal retail activity"
            retail_impact = "Normal shopping patterns"
        else:
            description = "Positive impact - Good shopping weather"
            retail_impact = "Increased foot traffic expected"
        
        return WeatherImpactResponse(
            location=weather['location'],
            weather_condition=weather['condition'],
            temperature=weather['temperature'],
            impact_score=impact_score,
            impact_description=description,
            retail_impact=retail_impact
        )
        
    except Exception as e:
        logger.error(f"Error analyzing weather impact: {e}")
        raise HTTPException(status_code=500, detail=f"Error analyzing weather: {str(e)}")


@router.get(
    "/one-call",
    summary="Get comprehensive weather data (One Call API)",
    description="Fetch current, hourly, daily forecasts and alerts"
)
async def get_one_call_weather(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    exclude: Optional[str] = Query(None, description="Comma-separated data to exclude (current,hourly,daily,alerts)")
):
    """
    Get comprehensive weather data using One Call API
    
    **Note:** Requires paid OpenWeatherMap tier
    
    **Parameters:**
    - `latitude`: Latitude
    - `longitude`: Longitude
    - `exclude`: Optional comma-separated list of data to exclude
    
    **Returns:**
    Comprehensive weather data including current, hourly, daily forecasts and alerts
    """
    try:
        service = get_weather_service()
        
        exclude_list = None
        if exclude:
            exclude_list = [e.strip() for e in exclude.split(',')]
        
        weather = service.get_one_call_weather(latitude, longitude, exclude_list)
        return weather
        
    except Exception as e:
        logger.error(f"Error fetching One Call weather: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching weather: {str(e)}")


@router.get(
    "/health",
    summary="Check weather service health",
    description="Verify weather API connectivity"
)
async def health_check():
    """
    Check weather service health and API key status
    
    **Returns:**
    Status information about the weather service
    """
    try:
        service = get_weather_service()
        
        return {
            "status": "healthy",
            "service": "OpenWeatherMap",
            "api_configured": not service._mock_mode,
            "units": service.units,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
