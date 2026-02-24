from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "FloodSense ML Service"
    app_version: str = "1.0.0"
    debug: bool = False
    openweather_api_key: str = ""
    models_dir: str = "app/models/saved"
    rf_model_path: str = "app/models/saved/rf_model.pkl"
    lstm_model_path: str = "app/models/saved/lstm_model.keras"
    preprocessor_path: str = "app/models/saved/preprocessor.pkl"
    label_encoder_path: str = "app/models/saved/label_encoder.pkl"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()