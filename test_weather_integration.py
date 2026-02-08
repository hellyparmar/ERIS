#!/usr/bin/env python
"""
Quick test script for OpenWeatherMap integration
Run: python test_weather_integration.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.services.weather_service import get_weather_service
from datetime import datetime


def test_weather_service():
    """Test weather service functionality"""
    
    print("\n" + "="*60)
    print("OpenWeatherMap Integration Test")
    print("="*60 + "\n")
    
    # Initialize service
    service = get_weather_service()
    
    print(f"✓ Service initialized")
    print(f"  - API Configured: {not service._mock_mode}")
    print(f"  - Units: {service.units}")
    print()
    
    # Test 1: Current weather
    print("TEST 1: Get Current Weather")
    print("-" * 60)
    try:
        weather = service.get_current_weather('Mumbai', 'IN')
        print(f"✓ Location: {weather['location']}")
        print(f"  - Temperature: {weather['temperature']}°C")
        print(f"  - Condition: {weather['condition']}")
        print(f"  - Humidity: {weather['humidity']}%")
        print(f"  - Wind Speed: {weather['wind_speed']} m/s")
        print(f"  - Is Mock Data: {weather.get('is_mock', False)}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False
    
    # Test 2: Forecast
    print("TEST 2: Get Weather Forecast")
    print("-" * 60)
    try:
        forecast = service.get_forecast('Mumbai', 'IN', days=3)
        print(f"✓ Location: {forecast['location']}")
        print(f"  - Forecast Count: {forecast['forecast_count']}")
        print(f"  - Sample forecasts:")
        for i, f in enumerate(forecast['forecasts'][:3]):
            print(f"    {i+1}. {f['timestamp'].strftime('%Y-%m-%d %H:%M')}: "
                  f"{f['temperature']}°C - {f['condition']}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False
    
    # Test 3: Weather Impact Analysis
    print("TEST 3: Weather Impact Analysis")
    print("-" * 60)
    try:
        impact = service.calculate_weather_impact('clear', 25)
        print(f"✓ Clear weather at 25°C:")
        print(f"  - Impact Score: {impact}")
        print(f"  - Interpretation: {'Positive' if impact > 1.0 else 'Negative'} impact on retail")
        
        impact_rain = service.calculate_weather_impact('rain', 20)
        print(f"\n✓ Rainy weather at 20°C:")
        print(f"  - Impact Score: {impact_rain}")
        print(f"  - Interpretation: {'Positive' if impact_rain > 1.0 else 'Negative'} impact on retail")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False
    
    # Test 4: Multi-location
    print("TEST 4: Multi-Location Weather")
    print("-" * 60)
    try:
        locations = [
            ('Mumbai', 'IN'),
            ('Delhi', 'IN'),
            ('Bangalore', 'IN'),
        ]
        weather_data = service.get_weather_for_retail_locations(locations)
        print(f"✓ Fetched weather for {len(weather_data)} locations:")
        for location, weather in list(weather_data.items())[:3]:
            print(f"  - {location}: {weather['temperature']}°C ({weather['condition']})")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False
    
    # Test 5: Weather by coordinates
    print("TEST 5: Weather by Coordinates")
    print("-" * 60)
    try:
        weather = service.get_current_weather_by_coordinates(19.076, 72.8777)
        print(f"✓ Coordinates (19.076, 72.8777):")
        print(f"  - Location: {weather['location']}")
        print(f"  - Temperature: {weather['temperature']}°C")
        print(f"  - Condition: {weather['condition']}")
        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")
        return False
    
    # Summary
    print("="*60)
    print("✓ All tests passed!")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("1. Start the API server: python api/main.py")
    print("2. Visit http://localhost:8000/docs for interactive API docs")
    print("3. Test endpoints:")
    print("   - GET /api/v1/weather/current?city=Mumbai")
    print("   - GET /api/v1/weather/forecast?city=Mumbai&days=5")
    print("   - POST /api/v1/weather/multi-location")
    print("4. Check docs/OPENWEATHER_INTEGRATION_GUIDE.md for full documentation")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = test_weather_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
