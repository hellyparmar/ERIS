# 🌤️ OpenWeatherMap Integration - Quick Start

## What's Been Implemented

A complete **OpenWeatherMap API integration** for your R-DIOS retail intelligence system with:

- ✅ Real-time weather data for any location
- ✅ 5-day weather forecasts
- ✅ Weather impact scoring for retail demand
- ✅ Multi-location batch requests
- ✅ REST API endpoints with Swagger docs
- ✅ Automatic fallback to mock data
- ✅ Production-ready error handling

## 5-Minute Setup

### 1️⃣ Get Free API Key (2 minutes)
```bash
# Go to https://openweathermap.org/api
# Sign up → Create account → Get API key
```

### 2️⃣ Add API Key to Environment (1 minute)
```bash
# Edit .env file
echo "OPENWEATHER_API_KEY=your_api_key_here" >> .env
```

### 3️⃣ Test It Works (2 minutes)
```bash
# Run test script
python test_weather_integration.py

# Output should show: ✓ All tests passed!
```

## Try It Out

### Start the API Server
```bash
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Test Weather Endpoints

**Option 1: Use cURL**
```bash
# Get current weather for Mumbai
curl "http://localhost:8000/api/v1/weather/current?city=Mumbai&country_code=IN"

# Get 5-day forecast for Delhi
curl "http://localhost:8000/api/v1/weather/forecast?city=Delhi&country_code=IN"

# Check service health
curl "http://localhost:8000/api/v1/weather/health"
```

**Option 2: Use Interactive API Docs**
```
Open http://localhost:8000/docs in your browser
Look for "weather" section to test all endpoints interactively
```

**Option 3: Python**
```python
from api.services.weather_service import get_weather_service

service = get_weather_service()
weather = service.get_current_weather('Mumbai', 'IN')
print(f"Temperature: {weather['temperature']}°C")
print(f"Condition: {weather['condition']}")
```

## Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/weather/current` | Current weather by city |
| GET | `/api/v1/weather/current/coordinates` | Current weather by lat/lon |
| GET | `/api/v1/weather/forecast` | 5-day forecast |
| POST | `/api/v1/weather/multi-location` | Weather for multiple stores |
| POST | `/api/v1/weather/impact-analysis` | Retail demand impact score |
| GET | `/api/v1/weather/health` | Service health check |

## Example: Weather Impact on Sales

```python
from api.services.weather_service import get_weather_service

service = get_weather_service()

# Get current weather
weather = service.get_current_weather('Mumbai', 'IN')

# Calculate impact multiplier
impact = service.calculate_weather_impact(
    weather['condition'],
    weather['temperature']
)

# Adjust demand forecast
base_forecast = 1000  # units
adjusted_forecast = base_forecast * impact

print(f"Base forecast: {base_forecast}")
print(f"Weather impact: {impact}")
print(f"Adjusted forecast: {adjusted_forecast}")
```

## Files Created/Updated

📁 **New Files:**
- `api/services/weather_service.py` - Core weather service (380 lines)
- `api/routers/weather.py` - REST API endpoints (380 lines)
- `test_weather_integration.py` - Test script
- `docs/OPENWEATHER_INTEGRATION_GUIDE.md` - Full documentation

📝 **Updated Files:**
- `api/main.py` - Added weather router
- `api/tasks/external_factors.py` - Updated to use weather service

## Free Tier Features

- ✅ 1,000 API calls per day
- ✅ Current weather & 5-day forecast
- ✅ Perfect for retail analytics
- ✅ No credit card required

## Next Steps

1. ✅ Set up API key
2. ✅ Run test script
3. ✅ Test API endpoints
4. Integrate with demand forecasting (see docs)
5. Add weather-based alerts
6. Create historical weather database

## Documentation

📖 **Full Guide:** [docs/OPENWEATHER_INTEGRATION_GUIDE.md](../docs/OPENWEATHER_INTEGRATION_GUIDE.md)

## Key Features

### Real-time Data
- Current temperature, humidity, wind speed
- Weather conditions (clear, rain, clouds, etc.)
- Visibility and pressure
- Sunrise/sunset times

### Demand Impact
- Automatic impact scoring (0.0-2.0 multiplier)
- Considers weather conditions AND temperature
- Ready for forecast integration

### Resilience
- Automatic mock data fallback
- Error handling for network issues
- Rate limit protection
- Detailed logging

### Production Ready
- Input validation
- Error responses
- Comprehensive logging
- Circuit breaker compatible
- Cache-friendly responses

## Support

- 📖 See `docs/OPENWEATHER_INTEGRATION_GUIDE.md` for full details
- 🧪 Run `test_weather_integration.py` to verify everything works
- 🔍 Check API docs at `/docs` endpoint

---

**That's it! You now have weather data integrated into your retail system. 🎉**
