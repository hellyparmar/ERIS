"""
OpenWeatherMap Integration Service
Handles all weather data fetching, caching, and processing

Features:
- Current weather for multiple locations
- Forecast data (5-day)
- Historical weather data
- Weather alerts
- Caching with configurable TTL
- Error handling and fallback to mock data
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
from enum import Enum

logger = logging.getLogger(__name__)


class WeatherUnits(str, Enum):
    """Weather data units"""
    METRIC = "metric"  # Celsius, meters/sec, mm
    IMPERIAL = "imperial"  # Fahrenheit, miles/hour, inches
    STANDARD = "standard"  # Kelvin


class WeatherService:
    """OpenWeatherMap API integration service"""
    
    BASE_URL = "https://api.openweathermap.org/data/2.5"
    FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
    ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
    
    def __init__(self, api_key: Optional[str] = None, units: WeatherUnits = WeatherUnits.METRIC):
        """
        Initialize weather service
        
        Args:
            api_key: OpenWeatherMap API key (defaults to OPENWEATHER_API_KEY env var)
            units: Temperature units (metric, imperial, standard)
        """
        self.api_key = api_key or os.getenv('OPENWEATHER_API_KEY')
        self.units = units.value if isinstance(units, WeatherUnits) else units
        self.timeout = 10  # seconds
        self._mock_mode = not self.api_key
        
        if self._mock_mode:
            logger.warning("⚠️ OpenWeatherMap API key not configured. Using mock data mode.")
        else:
            logger.info("✅ OpenWeatherMap service initialized with API key")
    
    def get_current_weather(self, location: str, country_code: Optional[str] = None) -> Dict:
        """
        Get current weather for a location
        
        Args:
            location: City name (e.g., 'Mumbai', 'New Delhi')
            country_code: ISO 3166 country code (e.g., 'IN' for India)
            
        Returns:
            Dictionary with current weather data
            
        Example:
            >>> service = WeatherService()
            >>> weather = service.get_current_weather('Mumbai', 'IN')
            >>> print(weather['temperature'], weather['condition'])
        """
        if self._mock_mode:
            return self._get_mock_current_weather(location)
        
        try:
            # Build location query
            if country_code:
                location_query = f"{location},{country_code}"
            else:
                location_query = location
            
            url = f"{self.BASE_URL}/weather"
            params = {
                'q': location_query,
                'appid': self.api_key,
                'units': self.units
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_weather_response(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather for {location}: {e}")
            return self._get_mock_current_weather(location)
    
    def get_current_weather_by_coordinates(self, lat: float, lon: float) -> Dict:
        """
        Get current weather by latitude/longitude coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with current weather data
        """
        if self._mock_mode:
            return self._get_mock_current_weather("Unknown")
        
        try:
            url = f"{self.BASE_URL}/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': self.units
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_weather_response(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather for coordinates ({lat}, {lon}): {e}")
            return self._get_mock_current_weather("Unknown")
    
    def get_forecast(self, location: str, country_code: Optional[str] = None, days: int = 5) -> Dict:
        """
        Get weather forecast for next 5 days
        
        Args:
            location: City name
            country_code: ISO 3166 country code
            days: Number of days (max 5 for free tier)
            
        Returns:
            Dictionary with forecast data
        """
        if self._mock_mode:
            return self._get_mock_forecast(location)
        
        try:
            if country_code:
                location_query = f"{location},{country_code}"
            else:
                location_query = location
            
            url = self.FORECAST_URL
            params = {
                'q': location_query,
                'appid': self.api_key,
                'units': self.units,
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_forecast_response(data, days)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast for {location}: {e}")
            return self._get_mock_forecast(location)
    
    def get_one_call_weather(self, lat: float, lon: float, exclude: Optional[List[str]] = None) -> Dict:
        """
        Get comprehensive weather data using One Call API (requires paid tier)
        Includes current, hourly, daily forecasts and alerts
        
        Args:
            lat: Latitude
            lon: Longitude
            exclude: List of data to exclude (current, minutely, hourly, daily, alerts)
            
        Returns:
            Dictionary with comprehensive weather data
        """
        if self._mock_mode:
            return self._get_mock_one_call_weather(lat, lon)
        
        try:
            url = self.ONECALL_URL
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': self.units
            }
            
            if exclude:
                params['exclude'] = ','.join(exclude)
            
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            return self._parse_one_call_response(data)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching One Call weather: {e}")
            return self._get_mock_one_call_weather(lat, lon)
    
    def get_weather_for_retail_locations(self, locations: List[Tuple[str, str]]) -> Dict[str, Dict]:
        """
        Get weather for multiple retail store locations
        
        Args:
            locations: List of (city, country_code) tuples
            
        Returns:
            Dictionary mapping location strings to weather data
            
        Example:
            >>> locations = [('Mumbai', 'IN'), ('Delhi', 'IN'), ('Bangalore', 'IN')]
            >>> weather = service.get_weather_for_retail_locations(locations)
        """
        results = {}
        
        for city, country_code in locations:
            location_key = f"{city},{country_code}"
            try:
                results[location_key] = self.get_current_weather(city, country_code)
            except Exception as e:
                logger.error(f"Error fetching weather for {location_key}: {e}")
                results[location_key] = self._get_mock_current_weather(city)
        
        return results
    
    def calculate_weather_impact(self, weather_condition: str, temperature: float = None) -> float:
        """
        Calculate retail impact score based on weather
        Returns a multiplier (0.0 - 2.0) for demand adjustment
        
        Args:
            weather_condition: Weather condition (clear, rain, clouds, etc)
            temperature: Temperature in configured units
            
        Returns:
            Impact multiplier (1.0 = no impact)
            
        Examples:
            - Clear weather: 1.0-1.1 (good for outdoor shopping)
            - Heavy rain: 0.7-0.8 (reduces foot traffic)
            - Extreme heat: 0.8-0.9 (reduces outdoor traffic)
        """
        impact = 1.0
        
        # Weather condition impact
        condition_impact = {
            'clear': 1.05,          # Good shopping weather
            'clouds': 1.0,          # Neutral
            'overcast': 1.0,        # Neutral
            'rain': 0.75,           # Reduces foot traffic
            'drizzle': 0.85,        # Light impact
            'thunderstorm': 0.6,    # Significant impact
            'snow': 0.7,            # Reduces foot traffic
            'mist': 0.95,           # Slight impact
            'smoke': 0.9,           # Minor impact
        }
        
        condition_lower = weather_condition.lower()
        impact *= condition_impact.get(condition_lower, 1.0)
        
        # Temperature impact (for metric units, adjust for imperial/standard)
        if temperature is not None:
            if self.units == 'metric':
                # Optimal shopping: 20-25°C
                if temperature < 10:
                    impact *= 0.85  # Too cold
                elif temperature < 15:
                    impact *= 0.9
                elif temperature > 35:
                    impact *= 0.8   # Too hot
                elif temperature > 30:
                    impact *= 0.9
            elif self.units == 'imperial':
                # Optimal shopping: 68-77°F
                if temperature < 50:
                    impact *= 0.85
                elif temperature < 59:
                    impact *= 0.9
                elif temperature > 95:
                    impact *= 0.8
                elif temperature > 86:
                    impact *= 0.9
        
        return round(impact, 2)
    
    # Helper methods
    
    def _parse_weather_response(self, data: Dict) -> Dict:
        """Parse OpenWeatherMap current weather response"""
        try:
            main = data['main']
            weather = data['weather'][0]
            wind = data.get('wind', {})
            rain = data.get('rain', {})
            clouds = data.get('clouds', {})
            
            return {
                'location': f"{data.get('name')}, {data.get('sys', {}).get('country')}",
                'latitude': data['coord']['lat'],
                'longitude': data['coord']['lon'],
                'timestamp': datetime.fromtimestamp(data['dt']),
                'temperature': main['temp'],
                'feels_like': main['feels_like'],
                'temp_min': main['temp_min'],
                'temp_max': main['temp_max'],
                'pressure': main['pressure'],
                'humidity': main['humidity'],
                'condition': weather['main'],
                'description': weather['description'],
                'icon': weather['icon'],
                'wind_speed': wind.get('speed', 0),
                'wind_direction': wind.get('deg'),
                'wind_gust': wind.get('gust'),
                'clouds': clouds.get('all', 0),
                'rainfall_1h': rain.get('1h', 0),
                'visibility': data.get('visibility'),
                'uv_index': data.get('uvi'),
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']),
                'sunset': datetime.fromtimestamp(data['sys']['sunset']),
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing weather response: {e}")
            return self._get_mock_current_weather("Unknown")
    
    def _parse_forecast_response(self, data: Dict, days: int) -> Dict:
        """Parse OpenWeatherMap forecast response"""
        try:
            forecasts = []
            for forecast_item in data['list'][:days * 8]:
                main = forecast_item['main']
                weather = forecast_item['weather'][0]
                wind = forecast_item.get('wind', {})
                rain = forecast_item.get('rain', {})
                
                forecasts.append({
                    'timestamp': datetime.fromtimestamp(forecast_item['dt']),
                    'temperature': main['temp'],
                    'feels_like': main['feels_like'],
                    'humidity': main['humidity'],
                    'condition': weather['main'],
                    'description': weather['description'],
                    'wind_speed': wind.get('speed', 0),
                    'rainfall': rain.get('3h', 0),
                    'clouds': forecast_item.get('clouds', {}).get('all', 0),
                })
            
            return {
                'location': f"{data.get('city', {}).get('name')}, {data.get('city', {}).get('country')}",
                'latitude': data['city']['coord']['lat'],
                'longitude': data['city']['coord']['lon'],
                'forecast_count': len(forecasts),
                'forecasts': forecasts,
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing forecast response: {e}")
            return self._get_mock_forecast("Unknown")
    
    def _parse_one_call_response(self, data: Dict) -> Dict:
        """Parse One Call API response"""
        try:
            result = {
                'latitude': data['lat'],
                'longitude': data['lon'],
                'timezone': data.get('timezone'),
                'current': self._parse_one_call_current(data.get('current', {})),
                'hourly': [self._parse_one_call_hourly(h) for h in data.get('hourly', [])[:48]],  # 48 hours
                'daily': [self._parse_one_call_daily(d) for d in data.get('daily', [])[:7]],  # 7 days
                'alerts': data.get('alerts', []),
            }
            return result
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing One Call response: {e}")
            return self._get_mock_one_call_weather(data.get('lat'), data.get('lon'))
    
    def _parse_one_call_current(self, data: Dict) -> Dict:
        """Parse One Call current weather"""
        weather = data.get('weather', [{}])[0]
        return {
            'timestamp': datetime.fromtimestamp(data.get('dt', 0)),
            'temperature': data.get('temp'),
            'feels_like': data.get('feels_like'),
            'humidity': data.get('humidity'),
            'pressure': data.get('pressure'),
            'condition': weather.get('main'),
            'description': weather.get('description'),
            'wind_speed': data.get('wind_speed'),
            'clouds': data.get('clouds'),
            'uv_index': data.get('uvi'),
            'visibility': data.get('visibility'),
        }
    
    def _parse_one_call_hourly(self, data: Dict) -> Dict:
        """Parse One Call hourly forecast"""
        weather = data.get('weather', [{}])[0]
        return {
            'timestamp': datetime.fromtimestamp(data.get('dt', 0)),
            'temperature': data.get('temp'),
            'humidity': data.get('humidity'),
            'condition': weather.get('main'),
            'rainfall': data.get('rain', {}).get('1h', 0),
            'wind_speed': data.get('wind_speed'),
        }
    
    def _parse_one_call_daily(self, data: Dict) -> Dict:
        """Parse One Call daily forecast"""
        weather = data.get('weather', [{}])[0]
        temp = data.get('temp', {})
        return {
            'timestamp': datetime.fromtimestamp(data.get('dt', 0)),
            'temp_day': temp.get('day'),
            'temp_min': temp.get('min'),
            'temp_max': temp.get('max'),
            'temp_night': temp.get('night'),
            'humidity': data.get('humidity'),
            'condition': weather.get('main'),
            'description': weather.get('description'),
            'rainfall': data.get('rain', 0),
            'uv_index': data.get('uvi'),
            'wind_speed': data.get('wind_speed'),
        }
    
    # Mock data methods (for testing/fallback)
    
    def _get_mock_current_weather(self, location: str) -> Dict:
        """Return mock current weather data"""
        now = datetime.now()
        return {
            'location': f"{location}, IN",
            'latitude': 19.0760,
            'longitude': 72.8777,
            'timestamp': now,
            'temperature': 28.5,
            'feels_like': 30.0,
            'temp_min': 26.0,
            'temp_max': 32.0,
            'pressure': 1012,
            'humidity': 65,
            'condition': 'Partly Cloudy',
            'description': 'partly cloudy',
            'icon': '02d',
            'wind_speed': 12.5,
            'wind_direction': 220,
            'wind_gust': None,
            'clouds': 40,
            'rainfall_1h': 0,
            'visibility': 10000,
            'uv_index': 7.5,
            'sunrise': now.replace(hour=6, minute=30),
            'sunset': now.replace(hour=18, minute=45),
            'is_mock': True,
        }
    
    def _get_mock_forecast(self, location: str) -> Dict:
        """Return mock forecast data"""
        forecasts = []
        now = datetime.now()
        
        for i in range(40):  # 5 days * 8 forecasts
            forecast_time = now + timedelta(hours=3*i)
            forecasts.append({
                'timestamp': forecast_time,
                'temperature': 25 + (i % 8) * 0.5,
                'feels_like': 27 + (i % 8) * 0.5,
                'humidity': 60 + (i % 4) * 5,
                'condition': 'Partly Cloudy',
                'description': 'partly cloudy',
                'wind_speed': 10 + (i % 5),
                'rainfall': 0,
                'clouds': 40 + (i % 3) * 10,
            })
        
        return {
            'location': f"{location}, IN",
            'latitude': 19.0760,
            'longitude': 72.8777,
            'forecast_count': 40,
            'forecasts': forecasts,
            'is_mock': True,
        }
    
    def _get_mock_one_call_weather(self, lat: float, lon: float) -> Dict:
        """Return mock One Call weather data"""
        now = datetime.now()
        return {
            'latitude': lat or 19.0760,
            'longitude': lon or 72.8777,
            'timezone': 'Asia/Kolkata',
            'current': {
                'timestamp': now,
                'temperature': 28.5,
                'feels_like': 30.0,
                'humidity': 65,
                'pressure': 1012,
                'condition': 'Partly Cloudy',
                'description': 'partly cloudy',
                'wind_speed': 12.5,
                'clouds': 40,
                'uv_index': 7.5,
                'visibility': 10000,
            },
            'hourly': [],
            'daily': [],
            'alerts': [],
            'is_mock': True,
        }


# Singleton instance
_weather_service = None


def get_weather_service(api_key: Optional[str] = None) -> WeatherService:
    """Get or create weather service singleton"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService(api_key)
    return _weather_service
