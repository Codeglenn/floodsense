import httpx
import asyncio
import pandas as pd
from datetime import datetime, timedelta
from app.core.logging import logger, setup_logging

setup_logging()


class WeatherDataFetcher:
    """
    Fetches weather data from Open-Meteo.
    Completely free, no API key needed, global coverage,
    historical data back to 1940, hourly granularity.
    """

    ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    HOURLY_VARIABLES = [
        "precipitation",
        "temperature_2m",
        "relative_humidity_2m",
        "surface_pressure",
        "wind_speed_10m",
        "soil_moisture_0_to_7cm",
        "soil_moisture_7_to_28cm",
    ]

    async def fetch_historical(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:

        logger.info(f"Fetching historical: ({lat}, {lon}) {start_date} to {end_date}")

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": self.HOURLY_VARIABLES,
            "timezone": "auto",
            "wind_speed_unit": "kmh",
            "precipitation_unit": "mm"
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(self.ARCHIVE_URL, params=params)
            response.raise_for_status()
            data = response.json()

        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        df["latitude"] = lat
        df["longitude"] = lon
        logger.info(f"Got {len(df)} records")
        return df

    async def fetch_forecast(self, lat: float, lon: float) -> pd.DataFrame:
        logger.info(f"Fetching 7-day forecast for ({lat}, {lon})")

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": self.HOURLY_VARIABLES,
            "forecast_days": 7,
            "timezone": "auto"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()

        df = pd.DataFrame(data["hourly"])
        df["time"] = pd.to_datetime(df["time"])
        return df


async def download_training_data():
    """
    Downloads 5 years of data for all 8 seeded regions.
    Run this ONCE. Saves to data/processed/training_data.csv.
    """
    fetcher = WeatherDataFetcher()

    regions = [
        {"name": "Houston",     "lat": 29.7604,  "lon": -95.3698},
        {"name": "NewOrleans",  "lat": 29.9511,  "lon": -90.0715},
        {"name": "Sacramento",  "lat": 38.5816,  "lon": -121.4944},
        {"name": "Bangladesh",  "lat": 23.6850,  "lon":  90.3563},
        {"name": "Mumbai",      "lat": 19.0760,  "lon":  72.8777},
        {"name": "Mekong",      "lat": 10.0452,  "lon": 105.7469},
        {"name": "Nairobi",     "lat": -1.2921,  "lon":  36.8219},
        {"name": "NileDelta",   "lat": 30.9000,  "lon":  30.8000},
    ]

    end_date   = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")

    all_dfs = []

    for region in regions:
        try:
            df = await fetcher.fetch_historical(
                lat=region["lat"],
                lon=region["lon"],
                start_date=start_date,
                end_date=end_date
            )
            df["region_name"] = region["name"]
            all_dfs.append(df)
            logger.info(f"Done: {region['name']} — {len(df)} rows")
            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Failed {region['name']}: {e}")

    combined = pd.concat(all_dfs, ignore_index=True)
    combined.to_csv("data/processed/training_data.csv", index=False)
    logger.info(f"Saved {len(combined)} total rows to data/processed/training_data.csv")
    return combined


if __name__ == "__main__":
    asyncio.run(download_training_data())