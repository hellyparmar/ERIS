import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import unittest
from datetime import date, timedelta
import pandas as pd
from unittest.mock import MagicMock, patch

from app.services.external_factors_service import ExternalFactorsService
from app.models.external_factors_models import ExternalFactor


class TestExternalFactorsService(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    def test_fetch_from_database(self):
        """Test normal fetch when data is present in the database (cached)."""
        from app.models.external_factors_models import EconomicIndicatorHistory
        mock_econ = EconomicIndicatorHistory(
            date=date(2024, 1, 1),
            cpi_inflation=5.5,
            wpi_inflation=3.2,
            food_inflation=6.1,
            repo_rate=6.5
        )
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_econ]
        
        service = ExternalFactorsService(db=self.mock_db, location="Mumbai")
        dates_to_fetch = [date(2024, 1, 1)]
        df = service.get_factors_for_dates(dates_to_fetch)
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['cpi_inflation'], 5.5)
        self.assertEqual(df.iloc[0]['repo_rate'], 6.5)

    @patch("app.services.weather_service.get_weather_service")
    def test_fallback_behavior_no_db(self, mock_weather_svc):
        """Test fallback when DB returns nothing and weather API fails (total source failure)."""
        mock_weather_svc.return_value.get_historical_weather.side_effect = Exception("API Unavailable")
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        service = ExternalFactorsService(db=self.mock_db)
        test_date = date(2024, 7, 15)
        df = service.get_factors_for_dates([test_date])
        
        self.assertFalse(df.empty)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['temperature_avg'], 28.0)
        self.assertEqual(df.iloc[0]['rainfall_mm'], 15.0)

    def test_holiday_fallback(self):
        """Test holiday fallback logic correctly identifies known holidays."""
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        service = ExternalFactorsService(db=self.mock_db)
        republic_day = date(2024, 1, 26)
        normal_day = date(2024, 2, 5)
        
        df = service.get_factors_for_dates([republic_day, normal_day])
        
        self.assertEqual(len(df), 2)
        republic_row = df[df['date'] == pd.to_datetime(republic_day)].iloc[0]
        normal_row = df[df['date'] == pd.to_datetime(normal_day)].iloc[0]
        
        self.assertEqual(republic_row['is_holiday'], 1)
        self.assertEqual(normal_row['is_holiday'], 0)


if __name__ == "__main__":
    unittest.main()

