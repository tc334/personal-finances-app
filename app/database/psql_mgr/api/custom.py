import logging
from uuid import UUID

from psycopg.rows import dict_row
from pydantic import BaseModel

from app.database.psql_mgr.psql_mgr import get_async_pool
from app.database.psql_mgr.utils.parse_schema import to_underscore

logger = logging.getLogger(__name__)


class CUSTOM_API:
    @staticmethod
    async def generic_query(query: str) -> list[dict]:
        async with (
            get_async_pool().connection() as conn,
            conn.cursor(row_factory=dict_row) as cur,
        ):
            await cur.execute(query)
            records = await cur.fetchall()
            if not records:
                raise RuntimeError("Fix me")
            return records

    @staticmethod
    async def generic_query_no_return(query: str):
        async with (
            get_async_pool().connection() as conn,
            conn.cursor(row_factory=dict_row) as cur,
        ):
            await cur.execute(query)

    @staticmethod
    async def delete_row(table: BaseModel, row_id: UUID | str):
        async with (
            get_async_pool().connection() as conn,
            conn.cursor(row_factory=dict_row) as cur,
        ):
            table_name = to_underscore(table.__name__)
            query = f"DELETE FROM {table_name} WHERE id='{str(row_id)}'"
            await cur.execute(query)
