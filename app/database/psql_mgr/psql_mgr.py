import asyncio
import logging
from functools import lru_cache

from psycopg.conninfo import make_conninfo
from psycopg_pool import AsyncConnectionPool

from app.utils.env_mgr import get_env

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_db_name() -> str:
    env = get_env()
    return env.RUN_ENV


@lru_cache(maxsize=1)
def get_schema_version() -> str:
    env = get_env()
    return env.PSQL_SCHEMA_VERSION


@lru_cache(maxsize=1)
def get_conn_info() -> str:
    env = get_env()

    return make_conninfo(
        user=env.PSQL_USER,
        password=env.PSQL_PASSWORD,
        host=env.PSQL_URL,
        port=env.PSQL_PORT,
        dbname=get_db_name(),
        sslmode="verify-full",
    )


@lru_cache(maxsize=1)
def get_async_pool() -> AsyncConnectionPool:
    a_pool = AsyncConnectionPool(
        conninfo=get_conn_info(),
        open=False,
        max_size=10,
    )
    logger.info("Created AsyncConnectionPool")
    return a_pool


async def start_async_pool():
    pool = get_async_pool()
    await pool.open()
    logger.info("Started AsyncConnectionPool")
    await pool.wait()
    logger.info("AsyncConnectionPool wait complete.")


async def reconnect_workers():
    a_pool = get_async_pool()
    while True:
        await asyncio.sleep(600)  # 10 minutes
        await a_pool.check()
        logger.info("Reconnected pool workers")


async def stop_async_pool():
    a_pool = get_async_pool()
    await a_pool.close()
    logger.info("Closed AsyncConnectionPool")
