# OpenWeatherMap Integration Guide

## Overview

This guide covers the complete integration of OpenWeatherMap API for real-time weather data in the R-DIOS retail intelligence system.

## Features

✅ **Real-time Weather Data**
- Current weather for any location
- Temperature, humidity, wind speed, pressure
- Weather conditions and descriptions
- Sunrise/sunset times

✅ **Weather Forecasting**
- 5-day forecast with 3-hour intervals
- Temperature trends
- Precipitation probability
- Wind data

✅ **Weather Impact Analysis**
- Retail demand impact scoring
- Weather-based demand adjustments
- Integration with sales forecasting

✅ **Multi-Location Support**
- Fetch weather for multiple stores in one request
- Batch processing for efficiency

✅ **Resilience Features**
- Fallback to mock data when API unavailable
- Error handling and logging
- Circuit breaker integration
- Rate limiting support

## Setup

### 1. Get OpenWeatherMap API Key

1. Visit [https://openweathermap.org/api](https://openweathermap.org/api)
2. Create a free account
3. Generate an API key from your account dashboard
4. Free tier includes:
   - 1,000 calls/day for current weather
   - 5-day forecast
   - 60-minute response time

### 2. Configure Environment Variables

Add to your `.env` file:

```env
# OpenWeatherMap Configuration
OPENWEATHER_API_KEY=your_api_key_here
```

Add to `.env.production`:

```env
OPENWEATHER_API_KEY=your_production_api_key_here
```

### 3. Verify Installation

All required dependencies are already in `requirements.txt`:
- `requests>=2.31.0` - HTTP library for API calls

## API Endpoints

### 1. Current Weather by Location

**Endpoint:** `GET /api/v1/weather/current`

**Parameters:**
- `city` (required): City name
- `country_code` (optional): ISO 3166 country code (default: "IN")

**Example:**
```bash
curl "http://localhost:8000/api/v1/weather/current?city=Mumbai&country_code=IN"
```

**Response:**
```json
{
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
  "visibility": 10000
}
```

### 2. Current Weather by Coordinates

**Endpoint:** `GET /api/v1/weather/current/coordinates`

**Parameters:**
- `latitude` (required): -90 to 90
- `longitude` (required): -180 to 180

**Example:**
```bash
curl "http://localhost:8000/api/v1/weather/current/coordinates?latitude=19.076&longitude=72.8777"
```

### 3. 5-Day Forecast

**Endpoint:** `GET /api/v1/weather/forecast`

**Parameters:**
- `city` (required): City name
- `country_code` (optional): ISO 3166 country code (default: "IN")
- `days` (optional): Number of days 1-5 (default: 5)

**Example:**
```bash
curl "http://localhost:8000/api/v1/weather/forecast?city=Mumbai&days=5"
```

### 4. Multi-Location Weather

**Endpoint:** `POST /api/v1/weather/multi-location`

**Request Body:**
```json
[
  {"city": "Mumbai", "country_code": "IN"},
  {"city": "Delhi", "country_code": "IN"},
  {"city": "Bangalore", "country_code": "IN"},
  {"city": "Hyderabad", "country_code": "IN"}
]
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/weather/multi-location" \
  -H "Content-Type: application/json" \
  -d '[
    {"city": "Mumbai", "country_code": "IN"},
    {"city": "Delhi", "country_code": "IN"}
  ]'
```

### 5. Weather Impact Analysis

**Endpoint:** `POST /api/v1/weather/impact-analysis`

**Parameters:**
- `city` (required): City name
- `country_code` (optional): ISO 3166 country code

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/weather/impact-analysis?city=Mumbai"
```

**Response:**
```json
{
  "location": "Mumbai, IN",
  "weather_condition": "Partly Cloudy",
  "temperature": 28.5,
  "impact_score": 1.05,
  "impact_description": "Positive impact - Good shopping weather",
  "retail_impact": "Increased foot traffic expected"
}
```

**Impact Score Interpretation:**
- `< 0.8`: Negative impact (bad weather)
- `0.8 - 1.0`: Slightly negative
- `1.0 - 1.2`: Neutral to positive
- `> 1.2`: Strong positive impact

### 6. Service Health Check

**Endpoint:** `GET /api/v1/weather/health`

**Example:**
```bash
curl "http://localhost:8000/api/v1/weather/health"
```

**Response:**
```json
{
  "status": "healthy",
  "service": "OpenWeatherMap",
  "api_configured": true,
  "units": "metric",
  "timestamp": "2025-02-07T15:30:00"
}
```

## Python Usage

### Basic Usage

```python
from api.services.weather_service import get_weather_service

# Initialize service
service = get_weather_service()

# Get current weather
weather = service.get_current_weather('Mumbai', 'IN')
print(f"Temperature: {weather['temperature']}°C")
print(f"Condition: {weather['condition']}")

# Get forecast
forecast = service.get_forecast('Mumbai', 'IN', days=5)
for f in forecast['forecasts']:
    print(f"{f['timestamp']}: {f['temperature']}°C - {f['condition']}")

# Calculate impact
impact = service.calculate_weather_impact(weather['condition'], weather['temperature'])
print(f"Retail impact multiplier: {impact}")
```

### Multi-Location Example

```python
from api.services.weather_service import get_weather_service

service = get_weather_service()

# Define store locations
locations = [
    ('Mumbai', 'IN'),
    ('Delhi', 'IN'),
    ('Bangalore', 'IN'),
    ('Chennai', 'IN')
]

# Get weather for all locations
weather_data = service.get_weather_for_retail_locations(locations)

for location, weather in weather_data.items():
    impact = service.calculate_weather_impact(
        weather['condition'],
        weather['temperature']
    )
    print(f"{location}: {weather['temperature']}°C ({weather['condition']}) - Impact: {impact}")
```

### With Custom Units

```python
from api.services.weather_service import WeatherService, WeatherUnits

# Initialize with imperial units (Fahrenheit)
service = WeatherService(units=WeatherUnits.IMPERIAL)

weather = service.get_current_weather('Mumbai')
print(f"Temperature: {weather['temperature']}°F")
```

## Integration with Demand Forecasting

### Example: Adjust Forecast Based on Weather

```python
from api.services.weather_service import get_weather_service
from api.services.ml_predictions import MLPredictionService

weather_service = get_weather_service()
ml_service = MLPredictionService()

# Get base forecast
base_forecast = ml_service.predict_demand('Mumbai')

# Get weather impact
weather = weather_service.get_current_weather('Mumbai', 'IN')
impact = weather_service.calculate_weather_impact(
    weather['condition'],
    weather['temperature']
)

# Adjust forecast
adjusted_forecast = base_forecast * impact

print(f"Base forecast: {base_forecast} units")
print(f"Weather impact: {impact}")
print(f"Adjusted forecast: {adjusted_forecast} units")
```

## Integration with Tasks/Celery

### Scheduled Weather Sync

The system includes Celery tasks for automated weather data synchronization:

```python
# In api/tasks/external_factors.py

@shared_task
def sync_weather():
    """Sync current weather data (runs hourly)"""
    db = SessionLocal()
    try:
        service = get_weather_service()
        weather = service.get_current_weather("Mumbai")
        
        weather_record = WeatherHistory(
            location="Mumbai",
            datetime=datetime.now(),
            temperature=weather['temperature'],
            humidity=weather['humidity'],
            condition=weather['condition'],
            ...
        )
        db.add(weather_record)
        db.commit()
        
        return {"status": "success"}
    finally:
        db.close()
```

## Caching Strategy

### Recommendations

For optimal performance and API rate limiting:

1. **Current Weather:** Cache for 10-15 minutes
2. **Forecast Data:** Cache for 30-60 minutes
3. **Historical Data:** Cache for 24 hours

### Implementation Example

```python
from functools import lru_cache
from datetime import datetime, timedelta

cache_timestamps = {}

def get_weather_cached(city, country_code='IN'):
    cache_key = f"{city}_{country_code}"
    
    # Check cache validity (15 minutes)
    if cache_key in cache_timestamps:
        if datetime.now() - cache_timestamps[cache_key] < timedelta(minutes=15):
            return cached_weather[cache_key]
    
    # Fetch fresh data
    service = get_weather_service()
    weather = service.get_current_weather(city, country_code)
    
    # Update cache
    cached_weather[cache_key] = weather
    cache_timestamps[cache_key] = datetime.now()
    
    return weather
```

## Error Handling

The service includes automatic fallback to mock data when:

1. API key is not configured
2. Network request fails
3. API response is invalid
4. Rate limit is exceeded

**Example with error handling:**

```python
from api.services.weather_service import get_weather_service
import logging

logger = logging.getLogger(__name__)

try:
    service = get_weather_service()
    weather = service.get_current_weather('Mumbai')
    
    if weather.get('is_mock'):
        logger.warning("Using mock weather data - API may be unavailable")
    
    print(weather)
    
except Exception as e:
    logger.error(f"Weather service error: {e}")
    # Application continues with fallback data
```

## Database Schema

### Weather History Table

If storing historical weather data:

```python
from sqlalchemy import Column, Integer, Float, String, DateTime

class WeatherHistory(Base):
    __tablename__ = "weather_history"
    
    id = Column(Integer, primary_key=True)
    location = Column(String(100), index=True)
    datetime = Column(DateTime, index=True)
    temperature = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Integer)
    pressure = Column(Integer)
    wind_speed = Column(Float)
    condition = Column(String(50))
    description = Column(String(200))
    rainfall = Column(Float)
    visibility = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Testing

### Test Current Weather Endpoint

```bash
# Get current weather
curl http://localhost:8000/api/v1/weather/current?city=Mumbai

# Get weather by coordinates
curl "http://localhost:8000/api/v1/weather/current/coordinates?latitude=19.076&longitude=72.8777"

# Get forecast
curl http://localhost:8000/api/v1/weather/forecast?city=Mumbai&days=5

# Check health
curl http://localhost:8000/api/v1/weather/health
```

### Python Tests

```python
import pytest
from api.services.weather_service import get_weather_service

def test_get_current_weather():
    service = get_weather_service()
    weather = service.get_current_weather('Mumbai', 'IN')
    
    assert 'temperature' in weather
    assert 'condition' in weather
    assert 'location' in weather

def test_calculate_weather_impact():
    service = get_weather_service()
    
    # Test clear weather
    impact = service.calculate_weather_impact('clear', 25)
    assert impact > 1.0
    
    # Test rainy weather
    impact = service.calculate_weather_impact('rain', 25)
    assert impact < 1.0

def test_forecast():
    service = get_weather_service()
    forecast = service.get_forecast('Mumbai', 'IN', days=5)
    
    assert forecast['forecast_count'] > 0
    assert len(forecast['forecasts']) > 0
```

## Monitoring and Logging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('api.services.weather_service')
```

### Log Levels

- `INFO`: API calls, successful data fetch
- `WARNING`: API key not configured, using mock data
- `ERROR`: Network errors, API failures
- `DEBUG`: Request/response details

## Rate Limiting

### Free Tier Limits

- **1,000 calls/day** for current weather
- **60 minute response time** (data can be up to 60 minutes old)
- **No hourly limit** (but monitor daily quota)

### Optimization Tips

1. Use multi-location endpoint for multiple cities
2. Cache results for 10-15 minutes
3. Use coordinates instead of city names when available
4. Schedule updates during off-peak hours

## Troubleshooting

### Issue: API key not working

```python
import os
from api.services.weather_service import get_weather_service

service = get_weather_service()
print(f"API Key configured: {not service._mock_mode}")
```

### Issue: Mock data being used

Ensure `OPENWEATHER_API_KEY` is set in environment:

```bash
echo $OPENWEATHER_API_KEY
```

### Issue: Rate limit exceeded

Check daily call count and implement caching:

```python
# Cache weather for 15 minutes to reduce API calls
from datetime import datetime, timedelta

last_fetch = {}
cached_data = {}

def get_weather_smart(city):
    if city in last_fetch:
        if datetime.now() - last_fetch[city] < timedelta(minutes=15):
            return cached_data[city]
    
    service = get_weather_service()
    data = service.get_current_weather(city)
    
    last_fetch[city] = datetime.now()
    cached_data[city] = data
    
    return data
```

## Pricing

- **Free Tier:** 1,000 calls/day - Perfect for testing and small deployments
- **Professional:** Pay as you go, ~$0.0005 per call
- **Enterprise:** Custom pricing

See [https://openweathermap.org/price](https://openweathermap.org/price) for details.

## Support Resources

- [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- [API Reference](https://openweathermap.org/current)
- [Status Page](https://status.openweathermap.org/)
- [Community Forum](https://openweathermap.org/forum)

## Next Steps

1. ✅ Set up API key
2. ✅ Test endpoints via Swagger UI (/docs)
3. ✅ Integrate with demand forecasting
4. ✅ Add scheduled weather sync tasks
5. ✅ Monitor API usage and costs
6. ✅ Implement caching strategy
7. ✅ Create alerts for extreme weather
