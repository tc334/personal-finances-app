import logging

from app.database.utils.env_mgr import get_env
from app.utils.log_helper import log_setup
from app.database.psql_mgr.psql_mgr import start_async_pool, stop_async_pool

logger = logging.getLogger(__name__)


async def start_services(
        app_name: str,
        start_psql_pool: bool = True,
        start_s3_client: bool = False,
):
    # formatting for loggers
    log_setup(app_name)

    # read .env file
    get_env()

    # PSQL DB
    if start_psql_pool:
        await start_async_pool()

    # S3 DB
    if start_s3_client:
        pass

    logger.info("Started all services")


async def stop_services():
    await stop_async_pool()

    logger.info("Stopped all services")
