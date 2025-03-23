import logging
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    RUN_ENV: str
    SECRET_KEY: str
    ADMIN_EMAIL: str
    S3_ENDPOINT: str
    S3_KEY_ID: str
    S3_APPLICATION_KEY: str
    PSQL_USER: str
    PSQL_PASSWORD: str
    PSQL_URL: str
    PSQL_PORT: str
    PSQL_SCHEMA_VERSION: str


@lru_cache(maxsize=1)
def get_env() -> Env:
    env = Env()
    logger.info("Reading .env file")
    return env
