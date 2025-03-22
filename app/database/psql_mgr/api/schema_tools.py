import os
import pathlib
from types import ModuleType

from psycopg.rows import dict_row

from app.database.psql_mgr.psql_mgr import get_async_pool, get_schema_version


async def get_db_name():
    async with (
        get_async_pool().connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        await cur.execute("SELECT current_database()")
        records = await cur.fetchone()
        return records["current_database"]


async def get_db_schema():
    async with (
        get_async_pool().connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        await cur.execute("SELECT current_schema()")
        records = await cur.fetchone()
        return records["current_schema"]


async def drop_schema():
    query = f"DROP SCHEMA IF EXISTS {get_schema_version()} CASCADE"
    async with get_async_pool().connection() as conn:
        await conn.execute(query)


async def create_schema(db_name: str, schema_version: str):
    async with get_async_pool().connection() as conn:
        await conn.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        await conn.execute(f"CREATE SCHEMA {schema_version};")


async def select_schema(schema_version: str):
    async with get_async_pool().connection() as conn:
        await conn.execute(f"ALTER USER home SET SEARCH_PATH = {schema_version};")


async def execute_sql_file(schema_module: ModuleType, env_schema_version):
    file_path = pathlib.Path(
        os.path.dirname(schema_module.__file__), f"{env_schema_version}.sql"
    )

    with open(file_path, "r", encoding="utf-8") as file:
        script = file.read()
        async with get_async_pool().connection() as conn:
            await conn.execute(script)
