import asyncio
import logging
from typing import Optional, TypeVar
from uuid import UUID

from psycopg.rows import class_row, dict_row
from psycopg.sql import SQL, Composed, Identifier, Placeholder
from pydantic import BaseModel

from app.database.utils.dict_helper import add_prefix_to_each_key
from app.database.utils.list_helper import make_list, remove_prefix_from_each_item
from app.database.psql_mgr.psql_mgr import get_async_pool
from app.database.psql_mgr.utils.parse_json import set_json_serdes, wrap_json_vals
from app.database.psql_mgr.utils.parse_schema import to_underscore
from app.database.utils.api_helper import check_return_all

logger = logging.getLogger(__name__)
set_json_serdes()


@staticmethod
async def _insert(
    row: BaseModel,
    return_cols: Optional[list[str]],
) -> BaseModel | dict | None:
    """
    Generic insert for ANY populated BaseModel.

    -> returns updated model or dict
    """
    assert isinstance(row, BaseModel)
    assert issubclass(row.__class__, BaseModel)
    assert return_cols is None or (
        isinstance(return_cols, list) and len(return_cols) > 0
    )

    table_name = to_underscore(row.__class__.__name__)
    pop_fields: dict = wrap_json_vals(row.model_dump(exclude_none=True))

    return_all = False
    if return_cols is not None:
        return_all = check_return_all(return_cols)
        return_cols = list(row.model_fields.keys()) if return_all else return_cols

    # possible queries
    base_query = "INSERT INTO {table} ({fields}) VALUES ({values}) "
    return_query = "RETURNING {ret_cols} "

    # always build up base insert query
    sql_base_query = SQL(base_query).format(
        table=Identifier(table_name),
        fields=SQL(", ").join(map(Identifier, pop_fields)),
        values=SQL(", ").join(map(Placeholder, pop_fields)),
    )
    query = Composed(sql_base_query)

    # build return query
    if return_cols is not None:
        sql_return_query = SQL(return_query).format(
            ret_cols=SQL(", ").join(map(Identifier, return_cols)),
        )
        query += Composed(sql_return_query)

    # execute query
    async with (
        get_async_pool().connection() as conn,
        conn.cursor(
            row_factory=class_row(row.__class__) if return_all else dict_row
        ) as cur,
    ):
        logger.debug(f"query: {query.as_string(cur)}")
        logger.debug(f"vals: {pop_fields}")

        await cur.execute(query, pop_fields)
        if return_cols is not None:
            record = await cur.fetchone()
            if not record:
                logger.error("No Record Found")
                raise RuntimeError("No Record Found")
            logger.debug(f"inserted row {record}")
            return record

        return None


# this auto types the return based on input
T = TypeVar("T")


class INSERT_API:
    @staticmethod
    async def insert_row(
        row: BaseModel,
    ) -> None:
        """
        inserts row

        --> returns populated BaseModel
        """
        await _insert(row=row, return_cols=None)

    @staticmethod
    async def insert_row_ret_model(
        row: T,
    ) -> T:
        """
        inserts row

        --> returns populated BaseModel
        """
        db_row = await _insert(row=row, return_cols=["*"])
        assert isinstance(db_row, BaseModel)
        return db_row

    @staticmethod
    async def insert_row_ret_uuid(
        row: BaseModel,
    ) -> UUID:
        """
        inserts row

        --> returns id
        """
        db_row = await _insert(row=row, return_cols=["id"])
        assert isinstance(db_row, dict)
        return db_row["id"]

    @staticmethod
    async def insert_row_ret_dict(
        row: BaseModel,
        return_cols: list[str] | str,
    ) -> dict:
        """
        inserts row

        --> returns dict
        """

        # allow for ret_cols input to be string or list
        return_cols = make_list(return_cols)
        assert return_cols[0] != "*", "use insert_row() instead"

        # The _insert method does not need table.col form for return_cols.
        # we need to undo the table, then add it back in after the call
        return_cols = remove_prefix_from_each_item(return_cols)

        db_row = await _insert(row=row, return_cols=return_cols)
        assert isinstance(db_row, dict)

        # now add table back to keys of dict
        db_row = add_prefix_to_each_key(db_row, to_underscore(row.__class__.__name__))

        return db_row

    @staticmethod
    async def tg_insert_rows(
        rows: list[BaseModel],
    ) -> None:
        """
        Async task group to insert many rows

        --> returns list of row BaseModels
        """
        assert isinstance(rows, list)
        assert len(rows) > 0
        assert isinstance(rows[0], BaseModel)

        async with asyncio.TaskGroup() as tg:
            _ = [tg.create_task(INSERT_API.insert_row(row)) for row in rows]

    @staticmethod
    async def tg_insert_rows_ret_model(
        rows: list[T],
    ) -> list[T]:
        """
        Async task group to insert many rows

        --> returns list of row BaseModels
        """
        assert isinstance(rows, list)
        assert len(rows) > 0
        assert isinstance(rows[0], BaseModel)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(INSERT_API.insert_row_ret_model(row)) for row in rows
            ]
        return [tsk.result() for tsk in tasks]

    @staticmethod
    async def tg_insert_rows_ret_uuids(
        rows: list[BaseModel],
    ) -> list[UUID]:
        """
        Async task group to insert many rows

        --> returns list of row ids
        """
        assert isinstance(rows, list)
        assert len(rows) > 0
        assert isinstance(rows[0], BaseModel)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(INSERT_API.insert_row_ret_uuid(row)) for row in rows
            ]
        return [tsk.result() for tsk in tasks]

    @staticmethod
    async def tg_insert_rows_ret_dict(
        rows: list[BaseModel],
        return_cols: list[str] | str,
    ) -> list[dict]:
        """
        Async task group to insert many rows

        --> returns list of dicts
        """
        assert isinstance(rows, list)
        assert len(rows) > 0
        assert isinstance(rows[0], BaseModel)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(INSERT_API.insert_row_ret_dict(row, return_cols))
                for row in rows
            ]
        return [tsk.result() for tsk in tasks]

    @staticmethod
    async def bulk_insert(
        rows: list[BaseModel],
    ) -> None:
        """
        Generic insert for ANY populated BaseModel.

        -> returns updated model or dict
        """
        assert isinstance(rows, list)
        assert all(isinstance(x, BaseModel) for x in rows)
        assert all(issubclass(row.__class__, BaseModel) for row in rows)

        # execute query
        async with (
            get_async_pool().connection() as conn,
            conn.cursor() as cur,
        ):
            table_name = to_underscore(rows[0].__class__.__name__)
            pop_fields = rows[0].model_dump(exclude_none=True).keys()
            values = []
            for row in rows:
                dumped: dict = wrap_json_vals(row.model_dump(exclude_none=True))
                values += list(dumped.values())

            n_fields = len(pop_fields)
            n_rows = len(rows)

            # possible queries
            base_query = "INSERT INTO {table} ({fields}) VALUES {values}"

            # always build up base insert query
            query = SQL(base_query).format(
                table=Identifier(table_name),
                fields=SQL(", ").join(map(Identifier, pop_fields)),
                values=SQL(", ").join(
                    [
                        Composed(
                            [
                                SQL("("),
                                SQL(", ").join(Placeholder() * n_fields),
                                SQL(")"),
                            ]
                        )
                        for _ in range(n_rows)
                    ]
                ),
            )

            logger.debug(f"query: {query.as_string(cur)}")
            logger.debug(f"vals: {values}")

            await cur.execute(query, values)
            return
