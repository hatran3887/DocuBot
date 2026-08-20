from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    database_url: PostgresDsn
    openai_api_key: str = Field(min_length=1)
    upload_dir: Path = Path('uploads')
    max_upload_size: int = 10 * 1024 * 1024
    app_name: str = 'Docubot'
    debug: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()