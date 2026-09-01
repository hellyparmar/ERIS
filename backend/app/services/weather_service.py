"""
Open-Meteo Integration Service
Handles all weather data fetching (forecast and historical) without API keys.
"""

import logging
import requests
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class WeatherService:
    """Open-Meteo API integration service"""
    
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    
    def __init__(self):
        self.timeout = 10
        logger.info("✅ Open-Meteo service initialized")
        
    def get_historical_weather(self, lat: float, lon: float, start_date: date, end_date: date) -> Dict[date, Dict]:
        """
        Get historical daily weather for a date range.
        Returns a dict mapping date to {'temperature_avg': float, 'rainfall_mm': float}
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'daily': 'temperature_2m_mean,precipitation_sum',
                'timezone': 'auto'
            }
            response = requests.get(self.ARCHIVE_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            if 'daily' in data:
                daily = data['daily']
                for i, d_str in enumerate(daily.get('time', [])):
                    d = datetime.fromisoformat(d_str).date()
                    temp = daily.get('temperature_2m_mean', [])[i]
                    rain = daily.get('precipitation_sum', [])[i]
                    if temp is not None and rain is not None:
                        result[d] = {
                            'temperature_avg': temp,
                            'rainfall_mm': rain
                        }
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching historical weather for {lat},{lon}: {e}")
            raise

    def get_forecast_weather(self, lat: float, lon: float, days: int = 7) -> Dict[date, Dict]:
        """
        Get daily forecast weather for upcoming days.
        Returns a dict mapping date to {'temperature_avg': float, 'rainfall_mm': float}
        """
        try:
            params = {
                'latitude': lat,
                'longitude': lon,
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'timezone': 'auto',
                'forecast_days': days
            }
            response = requests.get(self.FORECAST_URL, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            if 'daily' in data:
                daily = data['daily']
                for i, d_str in enumerate(daily.get('time', [])):
                    d = datetime.fromisoformat(d_str).date()
                    t_max = daily.get('temperature_2m_max', [])[i]
                    t_min = daily.get('temperature_2m_min', [])[i]
                    rain = daily.get('precipitation_sum', [])[i]
                    if t_max is not None and t_min is not None and rain is not None:
                        temp = (t_max + t_min) / 2.0
                        result[d] = {
                            'temperature_avg': temp,
                            'rainfall_mm': rain
                        }
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching forecast weather for {lat},{lon}: {e}")
            raise

    def get_current_weather(self, location: str, country_code: Optional[str] = None) -> Dict:
        """Dummy mock for compatibility with forecasting router"""
        now = datetime.now()
        return {
            'location': f"{location}, {country_code or 'IN'}",
            'latitude': 19.0760,
            'longitude': 72.8777,
            'timestamp': now,
            'temperature': 28.5,
            'condition': 'Clear',
        }

# Singleton instance
_weather_service = None

def get_weather_service() -> WeatherService:
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service

