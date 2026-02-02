"""
External Factor Integration Service
Thesis Week 7: Weather and Holiday integration for demand forecasting
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExternalFactorService:
    """
    Manages external factors for demand forecasting:
    - Weather data (temperature, precipitation, conditions)
    - Holiday calendar (Indian festivals, shopping events)
    - Economic indicators (CPI, fuel prices)
    """
    
    def __init__(self, data_path: str = 'data/transformed'):
        self.data_path = Path(data_path)
        self.weather_data = None
        self.holiday_data = None
        self.economic_data = None
    
    def load_weather_data(self, city: str = None) -> pd.DataFrame:
        """
        Load weather data from transformed dataset
        
        Args:
            city: Filter by city (optional)
        
        Returns:
            Weather DataFrame
        """
        weather_path = self.data_path / 'weather_data.csv'
        
        if weather_path.exists():
            self.weather_data = pd.read_csv(weather_path)
            self.weather_data['date'] = pd.to_datetime(self.weather_data['date'])
            
            if city:
                self.weather_data = self.weather_data[self.weather_data['city'] == city]
            
            logger.info(f"Loaded {len(self.weather_data)} weather records")
        else:
            # Generate synthetic weather
            self.weather_data = self._generate_synthetic_weather()
        
        return self.weather_data
    
    def _generate_synthetic_weather(self) -> pd.DataFrame:
        """Generate synthetic weather data for testing"""
        dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai']
        
        records = []
        for city in cities:
            base_temp = {'Mumbai': 28, 'Delhi': 25, 'Bangalore': 24, 'Chennai': 30}[city]
            
            for d in dates:
                # Seasonal variation
                if d.month in [12, 1, 2]:
                    temp = base_temp - 8 + np.random.uniform(-2, 2)
                elif d.month in [3, 4, 5]:
                    temp = base_temp + 5 + np.random.uniform(-2, 4)
                elif d.month in [6, 7, 8, 9]:
                    temp = base_temp - 2 + np.random.uniform(-3, 3)
                else:
                    temp = base_temp + np.random.uniform(-2, 2)
                
                # Monsoon precipitation
                if d.month in [6, 7, 8, 9]:
                    precip = np.random.uniform(5, 50) if np.random.random() < 0.6 else 0
                    condition = 'rainy' if precip > 0 else 'cloudy'
                else:
                    precip = np.random.uniform(0, 10) if np.random.random() < 0.1 else 0
                    condition = np.random.choice(['sunny', 'cloudy', 'partly_cloudy'])
                
                records.append({
                    'date': d,
                    'city': city,
                    'temperature_avg': round(temp, 1),
                    'temperature_high': round(temp + np.random.uniform(3, 8), 1),
                    'temperature_low': round(temp - np.random.uniform(3, 8), 1),
                    'precipitation_mm': round(precip, 1),
                    'humidity_percent': np.random.randint(40, 95) if d.month in [6, 7, 8, 9] else np.random.randint(30, 70),
                    'condition': condition
                })
        
        return pd.DataFrame(records)
    
    def load_holiday_data(self) -> pd.DataFrame:
        """Load holiday calendar with expected impact"""
        
        # Indian holidays with documented sales impact
        holidays = [
            # 2022
            {'date': '2022-01-26', 'name': 'Republic Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2022-03-18', 'name': 'Holi', 'type': 'religious', 'impact_multiplier': 1.25},
            {'date': '2022-05-03', 'name': 'Eid-ul-Fitr', 'type': 'religious', 'impact_multiplier': 1.30},
            {'date': '2022-08-15', 'name': 'Independence Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2022-10-05', 'name': 'Dussehra', 'type': 'religious', 'impact_multiplier': 1.20},
            {'date': '2022-10-24', 'name': 'Diwali', 'type': 'religious', 'impact_multiplier': 1.35},
            {'date': '2022-12-25', 'name': 'Christmas', 'type': 'religious', 'impact_multiplier': 1.25},
            
            # 2023
            {'date': '2023-01-26', 'name': 'Republic Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2023-03-08', 'name': 'Holi', 'type': 'religious', 'impact_multiplier': 1.25},
            {'date': '2023-04-22', 'name': 'Eid-ul-Fitr', 'type': 'religious', 'impact_multiplier': 1.30},
            {'date': '2023-08-15', 'name': 'Independence Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2023-10-24', 'name': 'Dussehra', 'type': 'religious', 'impact_multiplier': 1.20},
            {'date': '2023-11-12', 'name': 'Diwali', 'type': 'religious', 'impact_multiplier': 1.35},
            {'date': '2023-12-25', 'name': 'Christmas', 'type': 'religious', 'impact_multiplier': 1.25},
            
            # 2024
            {'date': '2024-01-26', 'name': 'Republic Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2024-03-25', 'name': 'Holi', 'type': 'religious', 'impact_multiplier': 1.25},
            {'date': '2024-04-10', 'name': 'Eid-ul-Fitr', 'type': 'religious', 'impact_multiplier': 1.30},
            {'date': '2024-08-15', 'name': 'Independence Day', 'type': 'national', 'impact_multiplier': 1.10},
            {'date': '2024-10-12', 'name': 'Dussehra', 'type': 'religious', 'impact_multiplier': 1.20},
            {'date': '2024-10-31', 'name': 'Diwali', 'type': 'religious', 'impact_multiplier': 1.35},
            {'date': '2024-12-25', 'name': 'Christmas', 'type': 'religious', 'impact_multiplier': 1.25},
        ]
        
        self.holiday_data = pd.DataFrame(holidays)
        self.holiday_data['date'] = pd.to_datetime(self.holiday_data['date'])
        
        # Add window (days before/after)
        self.holiday_data['window_start'] = self.holiday_data['date'] - timedelta(days=3)
        self.holiday_data['window_end'] = self.holiday_data['date'] + timedelta(days=1)
        
        logger.info(f"Loaded {len(self.holiday_data)} holidays")
        
        return self.holiday_data
    
    def load_economic_data(self) -> pd.DataFrame:
        """Load economic indicators"""
        economic_path = self.data_path / 'economic_indicators.csv'
        
        if economic_path.exists():
            self.economic_data = pd.read_csv(economic_path)
            self.economic_data['date'] = pd.to_datetime(self.economic_data['date'])
            logger.info(f"Loaded {len(self.economic_data)} economic records")
        else:
            self.economic_data = self._generate_synthetic_economic()
        
        return self.economic_data
    
    def _generate_synthetic_economic(self) -> pd.DataFrame:
        """Generate synthetic economic indicators"""
        dates = pd.date_range(start='2022-01-01', end='2024-12-31', freq='D')
        
        records = []
        base_cpi = 5.5
        base_petrol = 100.0
        base_usd = 82.0
        
        for i, d in enumerate(dates):
            trend = i / 365 * 0.02
            
            records.append({
                'date': d,
                'cpi_inflation': round(base_cpi + trend * 100 + np.random.uniform(-0.5, 0.5), 2),
                'fuel_price_petrol': round(base_petrol * (1 + trend + np.random.uniform(-0.02, 0.03)), 2),
                'usd_inr_rate': round(base_usd * (1 + trend * 0.5 + np.random.uniform(-0.005, 0.01)), 2)
            })
        
        return pd.DataFrame(records)
    
    def enrich_sales_data(
        self,
        sales_data: pd.DataFrame,
        date_column: str = 'date',
        city: str = 'Mumbai'
    ) -> pd.DataFrame:
        """
        Enrich sales data with external factors
        
        Args:
            sales_data: Sales DataFrame
            date_column: Date column name
            city: City for weather data
        
        Returns:
            Enriched DataFrame
        """
        # Ensure datetime
        sales_data[date_column] = pd.to_datetime(sales_data[date_column])
        
        # Load external data
        if self.weather_data is None:
            self.load_weather_data(city=city)
        
        if self.holiday_data is None:
            self.load_holiday_data()
        
        if self.economic_data is None:
            self.load_economic_data()
        
        # Filter weather for city
        weather = self.weather_data[self.weather_data['city'] == city].copy() if 'city' in self.weather_data.columns else self.weather_data.copy()
        weather['date'] = pd.to_datetime(weather['date'])
        
        # Merge weather
        enriched = sales_data.merge(
            weather[['date', 'temperature_avg', 'precipitation_mm', 'condition']],
            left_on=date_column,
            right_on='date',
            how='left',
            suffixes=('', '_weather')
        )
        
        # Add holiday flags
        enriched['is_holiday'] = False
        enriched['holiday_name'] = None
        enriched['holiday_impact'] = 1.0
        
        for _, holiday in self.holiday_data.iterrows():
            mask = (enriched[date_column] >= holiday['window_start']) & (enriched[date_column] <= holiday['window_end'])
            enriched.loc[mask, 'is_holiday'] = True
            enriched.loc[mask, 'holiday_name'] = holiday['name']
            enriched.loc[mask, 'holiday_impact'] = holiday['impact_multiplier']
        
        # Add monsoon flag
        enriched['is_monsoon'] = enriched[date_column].dt.month.isin([6, 7, 8, 9])
        
        # Merge economic data
        economic = self.economic_data.copy()
        economic['date'] = pd.to_datetime(economic['date'])
        
        enriched = enriched.merge(
            economic[['date', 'cpi_inflation', 'fuel_price_petrol']],
            left_on=date_column,
            right_on='date',
            how='left',
            suffixes=('', '_econ')
        )
        
        # Fill missing values
        enriched['temperature_avg'] = enriched['temperature_avg'].fillna(enriched['temperature_avg'].mean())
        enriched['precipitation_mm'] = enriched['precipitation_mm'].fillna(0)
        enriched['cpi_inflation'] = enriched['cpi_inflation'].fillna(enriched['cpi_inflation'].mean())
        
        # Create derived features
        enriched['is_weekend'] = enriched[date_column].dt.dayofweek.isin([5, 6])
        enriched['day_of_week'] = enriched[date_column].dt.dayofweek
        enriched['month'] = enriched[date_column].dt.month
        enriched['is_month_end'] = enriched[date_column].dt.day >= 25
        
        # Weather impact feature (bad weather = lower footfall)
        enriched['weather_impact'] = enriched.apply(
            lambda row: 0.85 if row.get('precipitation_mm', 0) > 20 else 
                       0.95 if row.get('precipitation_mm', 0) > 5 else 1.0,
            axis=1
        )
        
        logger.info(f"Enriched {len(enriched)} rows with external factors")
        
        return enriched
    
    def get_feature_importance(
        self,
        enriched_data: pd.DataFrame,
        target_column: str = 'revenue'
    ) -> Dict[str, float]:
        """
        Calculate correlation-based feature importance
        
        Returns:
            Dictionary of feature correlations with target
        """
        feature_cols = [
            'temperature_avg', 'precipitation_mm', 'is_holiday', 'is_monsoon',
            'is_weekend', 'day_of_week', 'month', 'cpi_inflation', 'weather_impact'
        ]
        
        correlations = {}
        
        for col in feature_cols:
            if col in enriched_data.columns:
                # Convert boolean to int for correlation
                if enriched_data[col].dtype == bool:
                    corr = enriched_data[col].astype(int).corr(enriched_data[target_column])
                else:
                    corr = enriched_data[col].corr(enriched_data[target_column])
                
                correlations[col] = round(corr, 3) if not pd.isna(corr) else 0
        
        # Sort by absolute correlation
        correlations = dict(sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True))
        
        logger.info(f"Feature correlations: {correlations}")
        
        return correlations
    
    def generate_future_features(
        self,
        start_date: date,
        days: int = 30,
        city: str = 'Mumbai'
    ) -> pd.DataFrame:
        """
        Generate future feature values for forecasting
        
        Args:
            start_date: Start date for predictions
            days: Number of days to generate
            city: City for weather assumptions
        
        Returns:
            DataFrame with future feature values
        """
        future_dates = pd.date_range(start=start_date, periods=days, freq='D')
        
        # Get upcoming holidays
        upcoming_holidays = self.holiday_data[
            (self.holiday_data['date'] >= pd.to_datetime(start_date)) & 
            (self.holiday_data['date'] <= pd.to_datetime(start_date) + timedelta(days=days))
        ] if self.holiday_data is not None else pd.DataFrame()
        
        records = []
        for d in future_dates:
            # Estimate weather based on month
            month = d.month
            if month in [12, 1, 2]:
                temp = 22 + np.random.uniform(-2, 2)
                precip = np.random.uniform(0, 5) if np.random.random() < 0.1 else 0
            elif month in [3, 4, 5]:
                temp = 32 + np.random.uniform(-2, 4)
                precip = np.random.uniform(0, 10) if np.random.random() < 0.15 else 0
            elif month in [6, 7, 8, 9]:
                temp = 28 + np.random.uniform(-3, 3)
                precip = np.random.uniform(10, 40) if np.random.random() < 0.5 else 0
            else:
                temp = 28 + np.random.uniform(-2, 2)
                precip = np.random.uniform(0, 5) if np.random.random() < 0.1 else 0
            
            # Check holidays
            is_holiday = False
            holiday_impact = 1.0
            for _, h in upcoming_holidays.iterrows():
                if h['window_start'] <= d <= h['window_end']:
                    is_holiday = True
                    holiday_impact = h['impact_multiplier']
                    break
            
            records.append({
                'ds': d,
                'date': d,
                'temperature_avg': temp,
                'precipitation_mm': precip,
                'is_holiday': is_holiday,
                'holiday_impact': holiday_impact,
                'is_monsoon': month in [6, 7, 8, 9],
                'is_weekend': d.dayofweek in [5, 6],
                'day_of_week': d.dayofweek,
                'month': month,
                'weather_impact': 0.85 if precip > 20 else 0.95 if precip > 5 else 1.0
            })
        
        future_df = pd.DataFrame(records)
        logger.info(f"Generated {len(future_df)} future feature rows")
        
        return future_df


# CLI for testing
if __name__ == "__main__":
    service = ExternalFactorService()
    
    # Load all external data
    weather = service.load_weather_data(city='Mumbai')
    print(f"Weather data: {len(weather)} rows")
    
    holidays = service.load_holiday_data()
    print(f"Holiday data: {len(holidays)} rows")
    
    economic = service.load_economic_data()
    print(f"Economic data: {len(economic)} rows")
    
    # Test enrichment with sample sales data
    sample_sales = pd.DataFrame({
        'date': pd.date_range(start='2023-01-01', end='2023-12-31', freq='D'),
        'revenue': np.random.uniform(40000, 60000, 365)
    })
    
    enriched = service.enrich_sales_data(sample_sales, city='Mumbai')
    print(f"\nEnriched columns: {list(enriched.columns)}")
    
    # Get feature importance
    importance = service.get_feature_importance(enriched)
    print(f"\nFeature importance:")
    for feat, corr in importance.items():
        print(f"  {feat}: {corr}")
    
    # Generate future features
    future = service.generate_future_features(date.today(), days=30)
    print(f"\nFuture features: {len(future)} days")
