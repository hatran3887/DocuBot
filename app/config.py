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
    embedding_model: str = 'text-embedding-3-small'
    embedding_dimensions: int = 1536
    embedding_batch_size: int = 100
    chat_model: str = 'gpt-4o-mini'
    chat_model_b: str = 'gpt-4.1-mini'
    comparison_enabled: bool = True
    chat_temperature: float = 0.0
    chat_max_tokens: int = 800

    cost_per_million: dict[str, tuple[float, float]] = {
        'gpt-4o-mini': (0.15, 0.60),
        'gpt-4.1-mini': (0.40, 1.60),
    }

    langfuse_public_key: str = ''
    langfuse_secret_key: str = ''
    langfuse_host: str = 'https://cloud.langfuse.com'
    langfuse_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore[call-arg]  # values come from environment


settings = get_settings()


# Configure the Langfuse client. Must happen before anything imports
# langfuse.openai, which builds its client at import time.
if settings.langfuse_enabled:
    from langfuse import Langfuse

    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )