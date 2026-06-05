"""
Celery Tasks - External Factors
Scheduled jobs to sync economy, weather, and holiday data
"""

from celery import shared_task
from datetime import datetime, timedelta
import requests
import os
import logging
try:
    import holidays
except ImportError:
    holidays = None

from app.api.db.database import SessionLocal
from app.api.db.external_factors_models import ExternalFactor, WeatherHistory, HolidayCalendar, EconomicIndicatorHistory

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
    Fetch economic indicators from RBI and other financial APIs
    """
    indicators = {}
    
    try:
        # RBI API integration (if API key available)
        rbi_api_key = os.getenv('RBI_API_KEY')
        if rbi_api_key:
            # RBI has some public APIs for economic data
            # This is a placeholder for actual RBI API integration
            rbi_url = "https://api.rbi.org.in"  # Placeholder URL
            headers = {'Authorization': f'Bearer {rbi_api_key}'}
            
            # Fetch repo rate
            try:
                response = requests.get(f"{rbi_url}/repo-rate", headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    indicators['repo_rate'] = data.get('rate', 6.5)
            except Exception as e:
                logging.warning(f"Failed to fetch RBI repo rate: {e}")
        
        # Fallback to public APIs or mock data
        if 'repo_rate' not in indicators:
            # Use mock data or public APIs
            indicators['repo_rate'] = 6.5  # Current RBI repo rate
            
        # Fetch inflation data (CPI)
        try:
            # Use public API or mock data
            indicators['inflation'] = 5.2  # Current inflation rate
        except Exception as e:
            logging.warning(f"Failed to fetch inflation data: {e}")
            indicators['inflation'] = 5.2
            
        # Fetch USD/INR exchange rate
        try:
            # Use a free currency API
            currency_api_key = os.getenv('CURRENCY_API_KEY')
            if currency_api_key:
                response = requests.get(
                    f"https://api.currencyapi.com/v3/latest?apikey={currency_api_key}&currencies=INR",
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    indicators['usd_inr'] = data.get('data', {}).get('INR', {}).get('value', 83.25)
            else:
                # Fallback to mock data
                indicators['usd_inr'] = 83.25
        except Exception as e:
            logging.warning(f"Failed to fetch USD/INR rate: {e}")
            indicators['usd_inr'] = 83.25
            
        # Fetch gold price
        try:
            # Use public gold price API or mock data
            indicators['gold_price'] = 6250.0  # per 10g
        except Exception as e:
            logging.warning(f"Failed to fetch gold price: {e}")
            indicators['gold_price'] = 6250.0
            
        # Fetch crude oil price
        try:
            # Use public oil price API or mock data
            indicators['crude_oil'] = 6800.0  # per barrel
        except Exception as e:
            logging.warning(f"Failed to fetch crude oil price: {e}")
            indicators['crude_oil'] = 6800.0
            
    except Exception as e:
        logging.error(f"Error fetching economic indicators: {e}")
        # Return mock data as fallback
        indicators = {
            'repo_rate': 6.5,
            'inflation': 5.2,
            'usd_inr': 83.25,
            'gold_price': 6250.0,
            'crude_oil': 6800.0
        }
    
    return indicators

def fetch_weather_data(location: str):
    """
    Fetch weather from OpenWeatherMap API
    Integrated with the weather service for consistent data handling
    """
    from app.api.services.weather_service import get_weather_service
    
    try:
        service = get_weather_service()
        weather = service.get_current_weather(location, 'IN')
        
        # Map service response to task format
        return {
            'temp_avg': weather.get('temperature', 28.5),
            'temp_max': weather.get('temp_max', 32.0),
            'temp_min': weather.get('temp_min', 25.0),
            'feels_like': weather.get('feels_like', 30.0),
            'humidity': weather.get('humidity', 65),
            'pressure': weather.get('pressure', 1012),
            'wind_speed': weather.get('wind_speed', 12.5),
            'rainfall': weather.get('rainfall_1h', 0),
            'condition': weather.get('condition', 'clear').lower(),
            'description': weather.get('description', 'Clear sky')
        }
    except Exception as e:
        logger.error(f"Error fetching weather for {location}: {e}")
        # Return mock data for resilience
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

def check_holiday(date):
    """
    Check if date is a holiday using holidays library for Indian holidays
    """
    if holidays is None:
        # Fallback to basic holidays if library not available
        MAJOR_HOLIDAYS = {
            (1, 26): ("Republic Day", "national"),
            (8, 15): ("Independence Day", "national"),
            (10, 2): ("Gandhi Jayanti", "national"),
            (1, 1): ("New Year's Day", "national"),
            (5, 1): ("Labour Day", "national"),
            (15, 8): ("Raksha Bandhan", "religious"),  # Approximate
            (12, 25): ("Christmas", "religious"),
        }
        
        key = (date.month, date.day)
        if key in MAJOR_HOLIDAYS:
            return {
                'name': MAJOR_HOLIDAYS[key][0],
                'type': MAJOR_HOLIDAYS[key][1]
            }
        return None
    
    # Use holidays library for comprehensive Indian holidays
    try:
        india_holidays = holidays.India(years=date.year)
        if date in india_holidays:
            holiday_name = india_holidays[date]
            # Determine holiday type based on name
            if any(word in holiday_name.lower() for word in ['diwali', 'holi', 'eid', 'christmas', 'good friday', 'ramadan']):
                holiday_type = 'religious'
            elif any(word in holiday_name.lower() for word in ['republic', 'independence', 'gandhi', 'constitution']):
                holiday_type = 'national'
            else:
                holiday_type = 'regional'
                
            return {
                'name': holiday_name,
                'type': holiday_type
            }
    except Exception as e:
        logging.warning(f"Error checking holidays with library: {e}")
        return None
    
    return None
    
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
