# OpenWeatherMap Integration - Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                              │
│  (Web Frontend, Mobile, External APIs, Data Analytics Tools)            │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI REST SERVER                                │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  API Routes (api/routers/)                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │       Weather Routes (api/routers/weather.py)              │  │   │
│  │  │  • GET  /api/v1/weather/current                            │  │   │
│  │  │  • GET  /api/v1/weather/forecast                           │  │   │
│  │  │  • POST /api/v1/weather/multi-location                     │  │   │
│  │  │  • POST /api/v1/weather/impact-analysis                    │  │   │
│  │  │  • GET  /api/v1/weather/health                             │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │                                                                    │   │
│  │  Other Routes (analytics, predictions, forecasting, etc.)         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                             │                                            │
│                             ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │            Business Logic Layer (Services)                       │   │
│  │  ┌────────────────────────────────────────────────────────────┐  │   │
│  │  │    WeatherService (api/services/weather_service.py)        │  │   │
│  │  │  • get_current_weather()                                   │  │   │
│  │  │  • get_forecast()                                          │  │   │
│  │  │  • get_weather_for_retail_locations()                      │  │   │
│  │  │  • calculate_weather_impact()                              │  │   │
│  │  │  • get_one_call_weather()                                  │  │   │
│  │  │  • Error handling & mock data fallback                     │  │   │
│  │  └────────────────────────────────────────────────────────────┘  │   │
│  │                                                                    │   │
│  │  Other Services (ML, Analytics, Cache, etc.)                      │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                    ▼                 ▼
   ┌──────────────────────────┐  ┌──────────────────────────┐
   │  OpenWeatherMap API      │  │  Cache Layer (Optional)  │
   │  (Real Weather Data)     │  │  (Redis/In-Memory)       │
   │                          │  │                          │
   │ • Current weather        │  │ • TTL: 10-15 minutes    │
   │ • Forecasts             │  │ • Reduces API calls     │
   │ • Weather alerts        │  │ • Improves response     │
   │ • Coordinates lookup    │  │                          │
   └──────────────────────────┘  └──────────────────────────┘
           ▲
           │
    HTTPS Requests
    (Encrypted)
           │
    ┌──────────────────────────────────────────────────────────┐
    │       OpenWeatherMap Cloud Service                       │
    │   (https://api.openweathermap.org)                       │
    │                                                          │
    │  • Real-time weather data for 200k+ locations          │
    │  • Worldwide coverage                                   │
    │  • 1000+ calls/day on free tier                        │
    │  • Backup data infrastructure                           │
    └──────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        REQUEST FLOW                                 │
└─────────────────────────────────────────────────────────────────────┘

Client Request:
  GET /api/v1/weather/current?city=Mumbai&country_code=IN
                    │
                    ▼
            ┌───────────────────┐
            │ FastAPI Router    │
            │ (weather.py)      │
            └─────────┬─────────┘
                    │
                    ▼
        ┌──────────────────────────┐
        │ Input Validation         │
        │ • Validate city name     │
        │ • Validate country code  │
        │ • Check bounds           │
        └────────┬─────────────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ Check Cache (Optional)     │
    │ • Found? → Return cached   │
    │ • Not found? → Continue    │
    └────────┬───────────────────┘
             │
             ▼
  ┌──────────────────────────────┐
  │ WeatherService               │
  │ .get_current_weather()       │
  └────────┬─────────────────────┘
           │
           ▼
  ┌──────────────────────────────┐
  │ API Key Check                │
  │ • Configured? → API call     │
  │ • Not configured? → Mock     │
  └────────┬─────────────────────┘
           │
    ┌──────┴──────┐
    │ API Key OK? │
    │             │
    ├─ YES ──────────────┐
    │                    │
    └─ NO ──────────────┐│
                        ││
                        ▼▼
              ┌─────────────────────┐
              │ OpenWeatherMap API  │  │ Mock Data
              │ HTTPS Request       │  │ (Fallback)
              │ • Build URL         │  │
              │ • Send request      │  │
              │ • Parse response    │  │
              └──────────┬──────────┘  │
                         │             │
                    ┌────┴─────┬───────┘
                    │          │
                    ▼          ▼
            ┌─────────────┐  ┌─────────────┐
            │ Success?    │  │ Mock Data   │
            └────┬────────┘  │ Ready       │
                 │           └─────────────┘
            ┌────┴────┐
            │          │
         YES │          │ NO
            │          │
            ▼          ▼
     ┌──────────┐  ┌──────────────┐
     │Real Data │  │Error Logging │
     └────┬─────┘  │Return Mock   │
          │        └──────┬───────┘
          │               │
          └───────┬───────┘
                  │
                  ▼
      ┌────────────────────────┐
      │ Parse Response         │
      │ • Extract fields       │
      │ • Format data          │
      │ • Add metadata         │
      └─────────┬──────────────┘
                │
                ▼
      ┌────────────────────────┐
      │ Cache Result (Optional)│
      │ • TTL: 15 minutes      │
      │ • Key: city_name       │
      └─────────┬──────────────┘
                │
                ▼
      ┌────────────────────────┐
      │ Return Response        │
      │ • JSON format          │
      │ • HTTP 200 OK          │
      │ • With metadata        │
      └─────────┬──────────────┘
                │
                ▼
           Client gets:
           {
             "location": "Mumbai, IN",
             "temperature": 28.5,
             "condition": "Partly Cloudy",
             ...
           }
```

## Integration Points

```
┌─────────────────────────────────────────────────────────────┐
│              Weather Data Integration Points                │
└─────────────────────────────────────────────────────────────┘

1. DEMAND FORECASTING
   ┌─────────────────────────────────────┐
   │ get_current_weather(city)           │
   │          ↓                          │
   │ calculate_weather_impact()          │
   │          ↓                          │
   │ Multiply forecast × impact_score    │
   │          ↓                          │
   │ Adjusted demand forecast            │
   └─────────────────────────────────────┘

2. EXTERNAL FACTORS SYNC (Celery Task)
   ┌─────────────────────────────────────┐
   │ Scheduled: Hourly/Daily             │
   │          ↓                          │
   │ fetch_weather_data() from service   │
   │          ↓                          │
   │ Store in WeatherHistory table       │
   │          ↓                          │
   │ Use for historical analysis         │
   └─────────────────────────────────────┘

3. RETAIL ANALYTICS DASHBOARD
   ┌─────────────────────────────────────┐
   │ Get weather for multiple stores     │
   │          ↓                          │
   │ Calculate regional impact scores    │
   │          ↓                          │
   │ Display weather widgets             │
   │          ↓                          │
   │ Show impact on sales patterns       │
   └─────────────────────────────────────┘

4. INVENTORY MANAGEMENT
   ┌─────────────────────────────────────┐
   │ Get weather forecast                │
   │          ↓                          │
   │ Adjust stock recommendations        │
   │ (e.g., more umbrellas in rain)     │
   │          ↓                          │
   │ Optimize inventory levels           │
   └─────────────────────────────────────┘

5. PROMOTIONAL CAMPAIGNS
   ┌─────────────────────────────────────┐
   │ Monitor weather conditions          │
   │          ↓                          │
   │ Trigger weather-based promotions    │
   │ (e.g., "stay cool" sales on hot    │
   │        days)                        │
   │          ↓                          │
   │ Increase relevance & conversion     │
   └─────────────────────────────────────┘
```

## Database Schema Integration

```
┌─────────────────────────────────────────────────────────┐
│              Weather Data Storage                       │
└─────────────────────────────────────────────────────────┘

WEATHER_HISTORY TABLE
┌──────────────────────────────────────┐
│ id (PK)                              │
│ location (VARCHAR)                   │
│ datetime (TIMESTAMP)                 │
│ temperature (FLOAT)                  │
│ humidity (INT)                       │
│ pressure (INT)                       │
│ wind_speed (FLOAT)                   │
│ condition (VARCHAR)                  │
│ rainfall (FLOAT)                     │
│ visibility (INT)                     │
│ created_at (TIMESTAMP)               │
│ updated_at (TIMESTAMP)               │
└──────────────────────────────────────┘

EXTERNAL_FACTORS TABLE
┌──────────────────────────────────────┐
│ id (PK)                              │
│ date (DATE)                          │
│ location (VARCHAR)                   │
│ temperature_avg (FLOAT)              │
│ temperature_max (FLOAT)              │
│ temperature_min (FLOAT)              │
│ humidity (INT)                       │
│ rainfall_mm (FLOAT)                  │
│ weather_condition (VARCHAR)          │
│ is_holiday (INT)                     │
│ is_weekend (INT)                     │
│ data_source (VARCHAR)                │
│ created_at (TIMESTAMP)               │
└──────────────────────────────────────┘

Relationships:
EXTERNAL_FACTORS.weather_condition 
    ← WEATHER_HISTORY.condition

EXTERNAL_FACTORS.location
    → Multiple WEATHER_HISTORY records
```

## Performance & Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│           Caching & Performance Layer                   │
└─────────────────────────────────────────────────────────┘

Request comes in
        │
        ▼
    ┌─────────────────────┐
    │ Check L1 Cache      │  (In-Memory/Redis)
    │ (TTL: 15 mins)      │  Fast! <1ms
    └────┬────────────────┘
         │
         ├─ HIT  ──→ Return immediately
         │
         └─ MISS ──→ API Call
                    │
                    ▼
               ┌─────────────────────┐
               │ OpenWeatherMap API  │  1-2 seconds
               │ (HTTPS Request)     │
               └────┬────────────────┘
                    │
                    ▼
              ┌──────────────┐
              │ Parse Result │
              └────┬─────────┘
                   │
                   ▼
            ┌──────────────────┐
            │ Store in Cache   │  (TTL: 15 minutes)
            └────┬─────────────┘
                 │
                 ▼
            ┌──────────────────┐
            │ Return to Client │
            └──────────────────┘

Cache Efficiency:
- Current Weather: Cache 10-15 mins
  (People check 4-6 times/hour)
- Forecast: Cache 30-60 mins
  (Changes infrequently)
- Coordinates: Cache 24 hours
  (Static reference)

Example API call savings:
- 1000 requests/day × 2 seconds = 33 mins saved
- Free tier: 1000 calls/day
- With caching (15 min TTL): ~100 actual calls needed
- Savings: ~90% reduction in API calls!
```

## Error Handling & Resilience

```
┌─────────────────────────────────────────────────────────┐
│         Error Handling & Resilience Flow                │
└─────────────────────────────────────────────────────────┘

API Request
        │
        ▼
Try to call OpenWeatherMap
        │
    ┌───┴────┬─────────────┬──────────────────┐
    │         │             │                  │
    ▼         ▼             ▼                  ▼
Network   API Key       Rate Limit       Timeout
Error     Error         Error            (>10s)
    │         │             │                  │
    └─────┬───┴─────────┬───┴──────────────┬──┘
          │             │                  │
          ▼             ▼                  ▼
    ┌────────────────────────────────────┐
    │ Log Error (Include details)         │
    │ • Error type                        │
    │ • Location requested                │
    │ • Timestamp                         │
    │ • Retry count                       │
    └─────────────┬──────────────────────┘
                  │
                  ▼
        ┌────────────────────┐
        │ Return Mock Data   │  (Fallback)
        │ • Realistic values │
        │ • With is_mock flag│
        │ • Log it           │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Client receives    │
        │ data (real or      │
        │ fallback) and      │
        │ continues working  │
        └────────────────────┘

Key Principle: Graceful Degradation
- System never fails, always returns data
- Real data preferred, mock acceptable
- Logging enables monitoring
- No API key = automatic mock mode
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│        Deployment & Environment Setup                   │
└─────────────────────────────────────────────────────────┘

Development Environment
┌─────────────────────────────────────┐
│ .env (Local)                        │
│ OPENWEATHER_API_KEY=dev_key         │
│ LOG_LEVEL=DEBUG                     │
└─────────────┬───────────────────────┘
              │
              ▼
        ┌─────────────┐
        │ FastAPI App │
        │ :8000       │
        └─────────────┘

Production Environment
┌─────────────────────────────────────┐
│ .env.production (Secure)            │
│ OPENWEATHER_API_KEY=prod_key        │
│ LOG_LEVEL=INFO                      │
│ CACHE_TTL=900 (15 mins)             │
└─────────────┬───────────────────────┘
              │
              ▼
        ┌──────────────────┐
        │ FastAPI + Uvicorn│
        │ Multiple workers │
        │ Behind Nginx     │
        └──────────────────┘
              │
              ▼
        ┌──────────────────┐
        │ CDN/Caching      │
        │ (if applicable)  │
        └──────────────────┘

Key Points:
✓ Different API keys for dev/prod
✓ Secrets managed via environment
✓ Never commit keys to git
✓ Use CI/CD to deploy safely
✓ Monitor API usage & costs
```

## Summary

The OpenWeatherMap integration follows a layered architecture:

1. **API Layer** - RESTful endpoints for client access
2. **Service Layer** - Business logic and API integration
3. **Cache Layer** - Performance optimization
4. **Data Layer** - Database storage and retrieval
5. **Resilience Layer** - Error handling and fallbacks
6. **Integration Points** - Multiple business use cases

This design ensures:
- ✅ Scalability
- ✅ Reliability
- ✅ Performance
- ✅ Maintainability
- ✅ Extensibility
