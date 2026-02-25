import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path
from app.core.logging import logger


class FloodFeatureEngineer:
    """
    Transforms raw hourly weather data into ML-ready features.

    Core hydrology insight:
    - Flood risk = accumulated moisture over time, not just current rainfall
    - Soil saturation prevents absorption → runoff → flooding
    - River levels lag rainfall by hours to days
    - Antecedent conditions matter as much as current conditions
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_columns = []
        self._fitted = False

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().sort_values("time").reset_index(drop=True)
        df["precipitation"] = df["precipitation"].fillna(0)

        # 1. Rolling rainfall accumulations 
        # Most important flood predictors. 72h captures multi-day events.
        df["rainfall_1h"]   = df["precipitation"]
        df["rainfall_3h"]   = df["precipitation"].rolling(3,   min_periods=1).sum()
        df["rainfall_6h"]   = df["precipitation"].rolling(6,   min_periods=1).sum()
        df["rainfall_12h"]  = df["precipitation"].rolling(12,  min_periods=1).sum()
        df["rainfall_24h"]  = df["precipitation"].rolling(24,  min_periods=1).sum()
        df["rainfall_48h"]  = df["precipitation"].rolling(48,  min_periods=1).sum()
        df["rainfall_72h"]  = df["precipitation"].rolling(72,  min_periods=1).sum()
        df["rainfall_7d"]   = df["precipitation"].rolling(168, min_periods=1).sum()

        # 2. Antecedent Precipitation Index (API) 
        # Classic hydrology metric. API_t = k * (API_{t-1} + P_t)
        # k=0.85 means yesterday's rain still has 85% weight today
        k = 0.85
        api = np.zeros(len(df))
        for i in range(1, len(df)):
            api[i] = k * (api[i - 1] + df["precipitation"].iloc[i])
        df["antecedent_precipitation_index"] = api

        # 3. Rainfall intensity metrics 
        # 30mm/hour burst is more dangerous than 30mm over 24 hours
        df["peak_intensity_6h"]        = df["precipitation"].rolling(6).max().fillna(0)
        df["peak_intensity_24h"]       = df["precipitation"].rolling(24).max().fillna(0)
        df["rainfall_variability_24h"] = df["precipitation"].rolling(24).std().fillna(0)

        # 4. Soil moisture features
        # Saturated soil cannot absorb more water → all becomes runoff
        sm1 = df["soil_moisture_0_to_7cm"].fillna(
            df["soil_moisture_0_to_7cm"].median()
        )
        sm2 = df.get("soil_moisture_7_to_28cm", sm1).fillna(sm1)

        df["soil_moisture_surface"]    = sm1
        df["soil_moisture_deep"]       = sm2
        df["soil_moisture_combined"]   = sm1 * 0.6 + sm2 * 0.4
        df["soil_moisture_change_6h"]  = df["soil_moisture_combined"].diff(6).fillna(0)
        df["soil_moisture_change_24h"] = df["soil_moisture_combined"].diff(24).fillna(0)

        # 5. Atmospheric conditions
        df["temperature"]        = df["temperature_2m"].fillna(
            df["temperature_2m"].median()
        )
        df["humidity"]           = df["relative_humidity_2m"].fillna(80)
        df["pressure"]           = df["surface_pressure"].fillna(1013)
        df["wind_speed"]         = df["wind_speed_10m"].fillna(0)
        df["pressure_change_6h"] = df["pressure"].diff(6).fillna(0)
        df["pressure_change_24h"]= df["pressure"].diff(24).fillna(0)

        # 6. Interaction features
        df["humidity_x_rainfall"] = df["humidity"] * df["rainfall_24h"] / 100
        df["heat_index"]          = df["temperature"] * df["humidity"] / 100

        # 7. Temporal features (cyclical encoding)
        # Jan (1) and Dec (12) are adjacent months, sin/cos captures this
        df["month"]           = df["time"].dt.month
        df["month_sin"]       = np.sin(2 * np.pi * df["month"] / 12)
        df["month_cos"]       = np.cos(2 * np.pi * df["month"] / 12)
        df["day_of_year"]     = df["time"].dt.dayofyear
        df["day_of_year_sin"] = np.sin(2 * np.pi * df["day_of_year"] / 365)
        df["day_of_year_cos"] = np.cos(2 * np.pi * df["day_of_year"] / 365)
        df["is_wet_season"]   = df["month"].isin([4, 5, 6, 9, 10, 11]).astype(int)

        self.feature_columns = [
            "rainfall_1h", "rainfall_3h", "rainfall_6h", "rainfall_12h",
            "rainfall_24h", "rainfall_48h", "rainfall_72h", "rainfall_7d",
            "antecedent_precipitation_index",
            "peak_intensity_6h", "peak_intensity_24h", "rainfall_variability_24h",
            "soil_moisture_surface", "soil_moisture_deep", "soil_moisture_combined",
            "soil_moisture_change_6h", "soil_moisture_change_24h",
            "temperature", "humidity", "pressure", "wind_speed",
            "pressure_change_6h", "pressure_change_24h",
            "humidity_x_rainfall", "heat_index",
            "month_sin", "month_cos",
            "day_of_year_sin", "day_of_year_cos",
            "is_wet_season"
        ]

        return df

    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assigns risk labels using World Meteorological Organization (WMO) heavy rainfall thresholds.
        In production: replace with actual historical flood event records.
        """
        conditions = [
            (df["rainfall_24h"] >= 150) | (df["rainfall_72h"] >= 300),
            (df["rainfall_24h"] >= 75)  | (df["rainfall_72h"] >= 150),
            (df["rainfall_24h"] >= 30)  |
            ((df["rainfall_24h"] >= 15) & (df["soil_moisture_combined"] > 0.35)),
        ]
        choices = ["CRITICAL", "HIGH", "MEDIUM"]
        df["risk_level"] = np.select(conditions, choices, default="LOW")

        risk_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        df["risk_label"] = df["risk_level"].map(risk_map)
        return df

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        X = df[self.feature_columns].fillna(0).values
        result = self.scaler.fit_transform(X)
        self._fitted = True
        return result

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        if not self._fitted:
            raise ValueError("Call fit_transform before transform")
        return self.scaler.transform(df[self.feature_columns].fillna(0).values)

    def save(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "scaler": self.scaler,
            "feature_columns": self.feature_columns,
            "fitted": self._fitted
        }, path)
        logger.info(f"Preprocessor saved to {path}")

    def load(self, path: str):
        data = joblib.load(path)
        self.scaler = data["scaler"]
        self.feature_columns = data["feature_columns"]
        self._fitted = data.get("fitted", True)
        logger.info(f"Preprocessor loaded from {path}")