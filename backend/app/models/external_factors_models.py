"""
External Factors Data Models
Track economy, weather, and holidays that impact retail sales
"""

from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, Enum as SQLEnum
from datetime import datetime as dt_datetime
import enum

from app.database import Base

class WeatherCondition(enum.Enum):
    """Weather conditions"""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    STORM = "storm"
    FOG = "fog"
    HOT = "hot"
    COLD = "cold"

class HolidayType(enum.Enum):
    """Holiday types"""
    NATIONAL = "national"
    RELIGIOUS = "religious"
    FESTIVAL = "festival"
    REGIONAL = "regional"
    SEASONAL = "seasonal"

class ExternalFactor(Base):
    """Daily external factors affecting retail"""
    __tablename__ = "external_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    
    # Economic Indicators (India-specific)
    repo_rate = Column(Float, comment="RBI repo rate %")
    inflation_rate = Column(Float, comment="CPI inflation %")
    usd_inr_rate = Column(Float, comment="USD to INR exchange rate")
    gold_price_10g = Column(Float, comment="Gold price per 10g in INR")
    crude_oil_price = Column(Float, comment="Crude oil price INR/barrel")
    
    # Weather Data
    location = Column(String(100), default="Mumbai", comment="City")
    temperature_avg = Column(Float, comment="Average temperature °C")
    temperature_max = Column(Float, comment="Max temperature °C")
    temperature_min = Column(Float, comment="Min temperature °C")
    humidity = Column(Float, comment="Humidity %")
    rainfall_mm = Column(Float, comment="Rainfall in mm")
    weather_condition = Column(SQLEnum(WeatherCondition))
    
    # Holiday/Event Information
    is_holiday = Column(Integer, default=0, comment="1 if holiday, 0 otherwise")
    holiday_name = Column(String(200), nullable=True)
    holiday_type = Column(SQLEnum(HolidayType), nullable=True)
    is_weekend = Column(Integer, default=0, comment="1 if Sat/Sun")
    
    # Special Events (festivals, sales days)
    is_festival_season = Column(Integer, default=0, comment="Diwali, Christmas, etc")
    festival_name = Column(String(100), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=dt_datetime.now)
    updated_at = Column(DateTime, default=dt_datetime.now, onupdate=dt_datetime.now)
    data_source = Column(Text, comment="JSON of data sources used")
    
    def __repr__(self):
        return f"<ExternalFactor date={self.date} location={self.location}>"

class EconomicIndicatorHistory(Base):
    """Historical economic indicators (for trend analysis)"""
    __tablename__ = "economic_indicators"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # RBI Data
    repo_rate = Column(Float)
    reverse_repo_rate = Column(Float)
    crr = Column(Float, comment="Cash Reserve Ratio %")
    slr = Column(Float, comment="Statutory Liquidity Ratio %")
    
    # Inflation
    cpi_inflation = Column(Float, comment="Consumer Price Index")
    wpi_inflation = Column(Float, comment="Wholesale Price Index")
    food_inflation = Column(Float)
    
    # Currency & Commodities
    usd_inr = Column(Float)
    eur_inr = Column(Float)
    gold_price = Column(Float)
    silver_price = Column(Float)
    crude_oil = Column(Float)
    
    # Stock Market
    sensex = Column(Float)
    nifty_50 = Column(Float)
    
    created_at = Column(DateTime, default=dt_datetime.now)
    
    def __repr__(self):
        return f"<EconomicIndicator date={self.date} repo_rate={self.repo_rate}>"

class WeatherHistory(Base):
    """Detailed weather history (multiple daily readings)"""
    __tablename__ = "weather_history"
    
    id = Column(Integer, primary_key=True, index=True)
    location = Column(String(100), nullable=False, index=True)
    datetime = Column(DateTime, nullable=False, index=True)
    
    temperature = Column(Float)
    feels_like = Column(Float)
    humidity = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
    rainfall = Column(Float)
    condition = Column(String(50))
    description = Column(Text)
    
    created_at = Column(DateTime, default=dt_datetime.now)
    
    def __repr__(self):
        return f"<Weather {self.location} @ {self.datetime} - {self.temperature}°C>"

class HolidayCalendar(Base):
    """Indian holidays and festivals calendar"""
    __tablename__ = "holiday_calendar"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    type = Column(SQLEnum(HolidayType), nullable=False)
    
    # Regional information
    is_national = Column(Integer, default=0)
    states_applicable = Column(Text, comment="Comma-separated state codes")
    
    # Business impact
    market_closed = Column(Integer, default=0, comment="Stock market closed")
    bank_holiday = Column(Integer, default=0)
    
    # Festival seasons (multi-day events)
    festival_season_start = Column(Date, nullable=True)
    festival_season_end = Column(Date, nullable=True)
    
    description = Column(Text)
    created_at = Column(DateTime, default=dt_datetime.now)
    
    def __repr__(self):
        return f"<Holiday {self.date} - {self.name}>"
