import logging
from types import ModuleType

from app.database.psql_mgr.api import schema_tools

logger = logging.getLogger(__name__)


async def drop_psql_schema(env_db_name: str, env_schema_version: str):
    cur_db = await schema_tools.get_db_name()
    cur_schema = await schema_tools.get_db_schema()

    assert cur_db == env_db_name
    #if cur_schema != env_schema_version:
    #    logger.warning(f"no matching schema to drop. DB: {cur_db}. Cur: {cur_schema}. Env: {env_schema_version}")
    #    return

    logger.info("Dropping schema")
    await schema_tools.drop_schema()


async def create_psql_schema_and_tables(
        env_db_name: str,
        env_schema_version: str,
        schema_module: ModuleType,
):
    # the schema you are trying to install better not already exist
    cur_schema = await schema_tools.get_db_schema()
    logger.info(f"current schema: {cur_schema}")
    assert cur_schema != env_schema_version

    logger.info(f"Creating schema: {env_db_name}, {env_schema_version}")
    await schema_tools.create_schema(env_db_name, env_schema_version)
    logger.info(f"created schema: {env_schema_version}")

    #
    await schema_tools.select_schema(env_schema_version)
    logger.info(f"Selected schema: {env_schema_version}")

    # verify success
    db_current = await schema_tools.get_db_name()
    cur_schema = await schema_tools.get_db_schema()
    logger.debug(f"Database. env: {env_db_name}, db: {db_current}\n"
                 f"Schemas. env:{env_schema_version}, db:{cur_schema}")
    assert cur_schema == env_schema_version
    logger.info("DB and ENV agree on schema")

    # tables
    logger.info("SQL file execution starting")
    await schema_tools.execute_sql_file(schema_module, env_schema_version)
    logger.info("SQL file execution complete")


async def rebuild_infra(
        env_db_name: str,
        env_schema_version: str,
        schema_module: ModuleType,
):
    # drop PSQL schema
    await drop_psql_schema(env_db_name, env_schema_version)

    # build models from schema

    # create schema
    await create_psql_schema_and_tables(env_db_name, env_schema_version, schema_module)
