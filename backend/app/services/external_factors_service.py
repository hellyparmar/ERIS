import logging
from datetime import date
from typing import List
import pandas as pd
from sqlalchemy.orm import Session

try:
    import holidays
except ImportError:
    holidays = None

from app.models.external_factors_models import ExternalFactor, EconomicIndicatorHistory

logger = logging.getLogger(__name__)

class ExternalFactorsService:
    """
    Centralized service for managing external factors (weather, holidays, economy)
    for forecasting models.
    """
    
    def __init__(self, db: Session, outlet_id: int = None, location: str = "Mumbai"):
        self.db = db
        self.outlet_id = outlet_id
        self.location = location

    def get_factors_for_dates(self, dates: List[date]) -> pd.DataFrame:
        if not dates:
            return pd.DataFrame()

        from app.models.external_factors_models import EconomicIndicatorHistory
        from sqlalchemy import func

        start_date = min(dates)
        end_date = max(dates)
        
        # 1. Determine location coords
        lat, lon = 19.0760, 72.8777 # default Mumbai
        if self.outlet_id:
            from app.models.outlet import Outlet
            outlet = self.db.query(Outlet).filter(Outlet.id == self.outlet_id).first()
            if outlet and outlet.latitude and outlet.longitude:
                lat, lon = outlet.latitude, outlet.longitude
                logger.info(f"Using actual outlet location: {lat}, {lon}")
            else:
                logger.info(f"Outlet {self.outlet_id} lacks lat/long. Using default {lat}, {lon}")

        # 2. Fetch live weather data
        from app.services.weather_service import get_weather_service
        weather_svc = get_weather_service()
        weather_data = {}
        
        past_dates = [d for d in dates if d <= date.today()]
        future_dates = [d for d in dates if d > date.today()]
        
        try:
            if past_dates:
                hist = weather_svc.get_historical_weather(lat, lon, min(past_dates), max(past_dates))
                weather_data.update(hist)
            if future_dates:
                fore = weather_svc.get_forecast_weather(lat, lon, len(future_dates))
                weather_data.update(fore)
        except Exception as e:
            logger.error(f"Live weather call failed, will use fallback: {e}")
        
        # 3. Query EconomicIndicatorHistory (monthly data, match by year/month)
        db_econ = self.db.query(EconomicIndicatorHistory).filter(
            func.date_trunc('month', EconomicIndicatorHistory.date) >= func.date_trunc('month', start_date),
            func.date_trunc('month', EconomicIndicatorHistory.date) <= func.date_trunc('month', end_date)
        ).all()
        
        econ_data = {
            (e.date.year, e.date.month): {
                'cpi_inflation': e.cpi_inflation or 0.0,
                'wpi_inflation': e.wpi_inflation or 0.0,
                'food_inflation': e.food_inflation or 0.0,
                'repo_rate': e.repo_rate or 0.0
            }
            for e in db_econ
        }

        records = []
        for d in dates:
            record = {'date': pd.to_datetime(d)}
            
            # Holiday
            record['is_holiday'] = 1 if self._check_holiday_fallback(d) else 0
            
            # Weather
            if d in weather_data:
                record['temperature_avg'] = weather_data[d].get('temperature_avg', 28.5)
                record['rainfall_mm'] = weather_data[d].get('rainfall_mm', 0.0)
            else:
                # Fallback seasonal estimate
                fallback = self._generate_fallback_for_date(d)
                record['temperature_avg'] = fallback['temperature_avg']
                record['rainfall_mm'] = fallback['rainfall_mm']
                
            # Economic indicators
            econ = econ_data.get((d.year, d.month), {'cpi_inflation': 5.0, 'wpi_inflation': 3.0, 'food_inflation': 6.0, 'repo_rate': 6.5})
            record.update(econ)
            
            records.append(record)

        df = pd.DataFrame(records)
        return df

    def _generate_fallback_for_date(self, d: date) -> dict:
        """Fallback logic when weather API fails."""
        month = d.month
        if month in [12, 1, 2]:
            temp = 22.0
            rain = 0.0
        elif month in [3, 4, 5]:
            temp = 32.0
            rain = 0.0
        elif month in [6, 7, 8, 9]:
            temp = 28.0
            rain = 15.0  # Monsoon
        else:
            temp = 28.0
            rain = 2.0
            
        return {
            'temperature_avg': temp,
            'rainfall_mm': rain,
        }

    def _check_holiday_fallback(self, d: date) -> bool:
        if holidays is not None:
            try:
                india_holidays = holidays.India(years=d.year)
                return d in india_holidays
            except Exception:
                pass
                
        # Hardcoded fallback
        major_holidays = [
            (1, 26), (8, 15), (10, 2), (1, 1), (5, 1), (12, 25)
        ]
        if (d.month, d.day) in major_holidays:
            return True
            
        # Approximation for floating holidays
        if d.month == 10 and 20 <= d.day <= 31: 
            return True
        if d.month == 3 and 10 <= d.day <= 25:
            return True
            
        return False
