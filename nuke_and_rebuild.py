import asyncio
import logging

from app.database.utils.service_mgr import start_services, stop_services
from app.database.psql_mgr.psql_mgr import get_db_name, get_schema_version
from app.database.utils.rebuild_infra import rebuild_infra
from app.database.psql_mgr import schema, models
from db_prefill import populate_infra

APP_NAME = "app"
logger = logging.getLogger(APP_NAME)


async def main():
    await start_services(app_name=APP_NAME)

    db_name = get_db_name()
    schema_version = get_schema_version()

    await rebuild_infra(db_name, schema_version, schema, models)
    await populate_infra()

    await stop_services()


if __name__ == '__main__':
    asyncio.run(main())
