"""
Celery Tasks - External Factors
Scheduled jobs to sync economy, weather, and holiday data
"""

from celery import shared_task
from datetime import datetime, timedelta
import requests
import os
import logging

from api.db.database import SessionLocal
from api.db.external_factors_models import ExternalFactor, WeatherHistory, HolidayCalendar, EconomicIndicatorHistory

logger = logging.getLogger(__name__)

@shared_task(name='api.tasks.external_factors.sync_daily_factors')
def sync_daily_factors():
    """
    Sync all daily external factors (economy + weather + holidays)
    Runs daily at 1 AM
    """
    db = SessionLocal()
    try:
        today = datetime.now().date()
        
        # Check if already synced
        existing = db.query(ExternalFactor).filter(
            ExternalFactor.date == today
        ).first()
        
        if existing:
            logger.info(f"External factors for {today} already synced")
            return {"status": "already_synced", "date": str(today)}
        
        # Fetch data from various sources
        economic_data = fetch_economic_indicators()
        weather_data = fetch_weather_data("Mumbai")
        holiday_data = check_holiday(today)
        
        # Create external factor record
        factor = ExternalFactor(
            date=today,
            # Economic
            repo_rate=economic_data.get('repo_rate'),
            inflation_rate=economic_data.get('inflation'),
            usd_inr_rate=economic_data.get('usd_inr'),
            gold_price_10g=economic_data.get('gold_price'),
            crude_oil_price=economic_data.get('crude_oil'),
            # Weather
            location="Mumbai",
            temperature_avg=weather_data.get('temp_avg'),
            temperature_max=weather_data.get('temp_max'),
            temperature_min=weather_data.get('temp_min'),
            humidity=weather_data.get('humidity'),
            rainfall_mm=weather_data.get('rainfall', 0),
            weather_condition=weather_data.get('condition'),
            # Holiday
            is_holiday=1 if holiday_data else 0,
            holiday_name=holiday_data.get('name') if holiday_data else None,
            holiday_type=holiday_data.get('type') if holiday_data else None,
            is_weekend=1 if today.weekday() >= 5 else 0,
            data_source='{"economy": "RBI", "weather": "OpenWeatherMap", "holidays": "Indian Calendar"}'
        )
        
        db.add(factor)
        db.commit()
        
        logger.info(f"✅ Synced external factors for {today}")
        return {"status": "success", "date": str(today)}
        
    except Exception as e:
        logger.error(f"Error syncing external factors: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@shared_task(name='api.tasks.external_factors.sync_weather')
def sync_weather():
    """
    Sync current weather data
    Runs every hour
    """
    db = SessionLocal()
    try:
        weather_data = fetch_weather_data("Mumbai")
        
        weather = WeatherHistory(
            location="Mumbai",
            datetime=datetime.now(),
            temperature=weather_data.get('temp_avg'),
            feels_like=weather_data.get('feels_like'),
            humidity=weather_data.get('humidity'),
            pressure=weather_data.get('pressure'),
            wind_speed=weather_data.get('wind_speed'),
            rainfall=weather_data.get('rainfall', 0),
            condition=weather_data.get('condition'),
            description=weather_data.get('description')
        )
        
        db.add(weather)
        db.commit()
        
        return {"status": "success", "temp": weather_data.get('temp_avg')}
        
    except Exception as e:
        logger.error(f"Error syncing weather: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

# Helper functions (to be implemented with actual APIs)

def fetch_economic_indicators():
    """
    Fetch economic indicators from RBI/financial APIs
    TODO: Implement actual RBI API integration
    """
    # Placeholder - in production, integrate with:
    # 1. RBI API for repo rate, CRR, SLR
    # 2. NSE/BSE for market indices
    # 3. Currency exchange APIs
    
    return {
        'repo_rate': 6.5,  # Mock data
        'inflation': 5.2,
        'usd_inr': 83.25,
        'gold_price': 6250.0,  # per 10g
        'crude_oil': 6800.0  # per barrel
    }

def fetch_weather_data(location: str):
    """
    Fetch weather from OpenWeatherMap API
    TODO: Implement actual API integration
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    
    if not api_key:
        logger.warning("OpenWeatherMap API key not configured. Using mock data.")
        return {
            'temp_avg': 28.5,
            'temp_max': 32.0,
            'temp_min': 25.0,
            'feels_like': 30.0,
            'humidity': 65,
            'pressure': 1012,
            'wind_speed': 12.5,
            'rainfall': 0,
            'condition': 'clear',
            'description': 'Clear sky'
        }
    
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={location},IN&appid={api_key}&units=metric"
        response = requests.get(url, timeout=5)
        data = response.json()
        
        return {
            'temp_avg': data['main']['temp'],
            'temp_max': data['main']['temp_max'],
            'temp_min': data['main']['temp_min'],
            'feels_like': data['main']['feels_like'],
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': data['wind']['speed'],
            'rainfall': data.get('rain', {}).get('1h', 0),
            'condition': data['weather'][0]['main'].lower(),
            'description': data['weather'][0]['description']
        }
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        return fetch_weather_data.__defaults__[0]  # Return mock data

def check_holiday(date):
    """
    Check if date is a holiday
    TODO: Import Indian holiday calendar
    """
    # Major Indian holidays (simplified - use holidays library in production)
    MAJOR_HOLIDAYS = {
        (1, 26): ("Republic Day", "national"),
        (8, 15): ("Independence Day", "national"),
        (10, 2): ("Gandhi Jayanti", "national"),
        # Add Diwali, Holi, etc (lunar calendar requires holidays library)
    }
    
    key = (date.month, date.day)
    if key in MAJOR_HOLIDAYS:
        return {
            'name': MAJOR_HOLIDAYS[key][0],
            'type': MAJOR_HOLIDAYS[key][1]
        }
    
    return None

@shared_task(name='api.tasks.external_factors.backfill_historical')
def backfill_historical_data(start_date: str, end_date: str):
    """
    Backfill historical external factors
    Usage: backfill_historical_data.delay('2024-01-01', '2024-12-31')
    """
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        current = start
        count = 0
        
        while current <= end:
            # Check if already exists
            existing = db.query(ExternalFactor).filter(
                ExternalFactor.date == current
            ).first()
            
            if not existing:
                # Create placeholder record
                factor = ExternalFactor(
                    date=current,
                    location="Mumbai",
                    is_weekend=1 if current.weekday() >= 5 else 0,
                    data_source='{"backfill": true}'
                )
                db.add(factor)
                count += 1
            
            current += timedelta(days=1)
        
        db.commit()
        logger.info(f"✅ Backfilled {count} days from {start_date} to {end_date}")
        return {"status": "success", "days_added": count}
        
    except Exception as e:
        logger.error(f"Error backfilling: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
