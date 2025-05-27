import asyncio
import logging
from dataclasses import dataclass
from inspect import getmembers
from typing import Any, Optional
from uuid import UUID

from psycopg.rows import dict_row
from psycopg.sql import SQL, Composed, Identifier, Literal, Placeholder
from pydantic import BaseModel

from app.database.utils import dict_helper as dh
from app.database.utils import list_helper as lh
from app.database.psql_mgr.psql_mgr import get_async_pool
from app.database.psql_mgr.utils.parse_json import set_json_serdes
from app.database.psql_mgr.utils.parse_schema import to_underscore
from app.database.utils.api_helper import check_return_all

logger = logging.getLogger(__name__)
set_json_serdes()


class NoRecordsFoundError(Exception):
    pass


def is_agg_col(potential_agg_col: str) -> bool:
    words = potential_agg_col.split(".")
    return len(words) == 3 and any(
        words[0] in x for x in getmembers(FETCH_API.agg_funcs)
    )


def split_agg_col(agg_col: str) -> tuple[str, str]:
    assert is_agg_col(agg_col)
    words = agg_col.split(".")

    agg_func = words[0]
    col_name = f"{words[1]}.{words[2]}"
    return agg_func, col_name


def get_agg_col_func(agg_col: str) -> str:
    agg_func, _ = split_agg_col(agg_col)
    return agg_func


def get_agg_col_name(agg_col: str) -> str:
    _, col_name = split_agg_col(agg_col)
    return col_name


def flatten(rows: list, select_cols: list | str):
    assert lh.is_valid_list(rows)
    assert all(isinstance(row, (BaseModel, dict)) for row in rows)
    select_cols = lh.make_list(select_cols)

    # nice return helpers
    if len(rows) == 1:
        if len(select_cols) == 1 and select_cols[0] != "*":
            # flatten dict, return val only
            return rows[0][select_cols[0]]
        return rows[0]
    if len(rows) > 1 and len(select_cols) == 1 and select_cols[0] != "*":
        # flatten list of dicts with only one element to just list
        return [row[select_cols[0]] for row in rows]
    return rows


def add_equal_where_operator(
    where_dict: dict[str, Any] | dict[str, tuple[str, Any]],
):
    ret_dict = {}
    for k, v in where_dict.items():
        # allow for default operator to be EQUAL, add it if not specified
        if not isinstance(v, tuple) or (
            isinstance(v, tuple)
            and v[0]
            not in [
                v
                for k, v in getmembers(FETCH_API.where_operator)
                if not k.startswith("__")
            ]
        ):
            ret_dict[k] = (FETCH_API.where_operator.EQUAL, v)
        else:
            ret_dict[k] = v

    return ret_dict


def format_val_dict(
    where_dict: Optional[dict[str, tuple[str, Any]]],
):
    """remove where operator and other formatting"""
    if where_dict is None:
        return None

    val_dict = {}
    for k, v in where_dict.items():
        # break up between tuple into low and high keys
        if v[0] == FETCH_API.where_operator.BETWEEN:
            val_dict[f"{k}.low"] = v[1][0]
            val_dict[f"{k}.high"] = v[1][1]
        else:
            val_dict[k] = v[1]

    return val_dict


def compose_all_where_possibilities(where_dict: dict[str, tuple[str, Any]]) -> list:
    where_list = []

    for k, v in where_dict.items():
        if v[0] in [
            FETCH_API.where_operator.EQUAL,
            FETCH_API.where_operator.GREATER_THAN,
            FETCH_API.where_operator.LESS_THAN,
            FETCH_API.where_operator.GREATER_THAN_OR_EQUAL_TO,
            FETCH_API.where_operator.LESS_THAN_OR_EQUAL_TO,
        ]:
            where_list.append(
                Composed(
                    [
                        Identifier(*(k.split("."))),
                        SQL(f" {v[0]} "),
                        Placeholder(k),
                    ],
                )
            )
        elif v[0] == FETCH_API.where_operator.IN:
            where_list.append(
                Composed(
                    [
                        Identifier(*(k.split("."))),
                        SQL(" = "),
                        SQL("ANY"),
                        SQL("("),
                        Placeholder(k),
                        SQL(")"),
                    ],
                )
            )
        elif v[0] == FETCH_API.where_operator.BETWEEN:
            where_list.append(
                Composed(
                    [
                        Identifier(*(k.split("."))),
                        SQL(f" {v[0]} "),
                        Placeholder(f"{k}.low"),
                        SQL(" AND "),
                        Placeholder(f"{k}.high"),
                    ],
                )
            )
        else:
            raise RuntimeError("unknown Where Operator")

    return where_list


async def _fetch(
    select_cols: list[str],
    from_table: BaseModel,
    join_tables: Optional[list[BaseModel]],
    join_on: Optional[list[tuple[str, str]]],
    where_dict: Optional[dict[str, tuple[str, Any]]],
    group_by: Optional[list[str]],
    order_by: Optional[list[tuple[str, str]]],
    limit: Optional[int],
) -> BaseModel | dict:
    # pylint: disable-msg=too-many-locals

    """Generic Fetch
    - select_cols: table.col to return
    - aggreg_cols: list of (function, col) tuple
    - from_table: table to query
    - join_table: list of tables to inner join
    - join_on: list of tuples pairs of keys to join
    - where_dict: {columns: (operator, value)} to filter table rows on
    - group_by: list of cols to group on
    - order_by: list of tuples of cols and direction (ASC|DESC)
    - limit: int rows to return

    -> returns either model or dict if return_cols is not "*"
    """
    # allow for list or single element
    select_cols = lh.make_list(select_cols)
    join_tables = lh.make_list(join_tables)
    join_on = lh.make_list(join_on)
    group_by = lh.make_list(group_by)
    order_by = lh.make_list(order_by)

    # validate from_table
    assert issubclass(from_table, BaseModel)
    table_name = to_underscore(from_table.__name__)

    # validate select_cols
    assert lh.is_valid_list(select_cols)
    return_all = check_return_all(select_cols)
    select_cols = (
        lh.add_prefix_to_each_item(list(from_table.model_fields.keys()), table_name)
        if return_all
        else select_cols
    )
    assert all(
        len(col.split(".")) == 2 or (len(col.split(".")) == 3 and is_agg_col(col))
        for col in select_cols
    ), "expecting 'table.col' or 'agg.table.col'"

    # validate join_tables and join_on
    assert (join_tables is None and join_on is None) or (
        lh.is_valid_list(join_tables) and lh.is_valid_list(join_on)
    )

    if join_tables is not None:
        assert len(join_tables) > 0 and len(join_on) > 0
        assert len(join_tables) == len(join_on)
        for table, on_tuple in zip(join_tables, join_on):
            assert issubclass(table, BaseModel)
            assert isinstance(on_tuple, tuple)
            assert len(on_tuple[0].split(".")) == 2, "expecting 'table.col'"
            assert len(on_tuple[1].split(".")) == 2, "expecting 'table.col'"

    # validate where_dict
    assert where_dict is None or dh.is_valid_dict(where_dict)
    if where_dict is not None:
        assert all(len(k.split(".")) == 2 for k in where_dict), "exp 'table.col'"
        where_dict = add_equal_where_operator(where_dict)
        assert all(
            isinstance(x, tuple)
            and x[0]
            in [
                v
                for k, v in getmembers(FETCH_API.where_operator)
                if not k.startswith("__")
            ]
            for x in where_dict.values()
        ), "where dict not in correct form { key: (operator, value) }"
        assert all(
            isinstance(x[1], list)
            for x in where_dict.values()
            if x[0] == FETCH_API.where_operator.IN
        ), "use list type for IN operator"
        assert all(
            isinstance(x[1], tuple) and len(x[1]) == 2
            for x in where_dict.values()
            if x[0] == FETCH_API.where_operator.BETWEEN
        ), "use tuple of len 2 for BETWEEN operator"

    # validate group_by
    assert group_by is None or lh.is_valid_list(group_by)
    if group_by is not None:
        assert all(
            len(col.split(".")) == 2 or (len(col.split(".")) == 3 and is_agg_col(col))
            for col in group_by
        ), "expecting 'table.col' or 'agg.table.col'"

    # validate order_by
    assert order_by is None or lh.is_valid_list(order_by)
    if order_by is not None:
        assert all(
            isinstance(x, tuple)
            and isinstance(x[0], str)
            and (
                len(x[0].split(".")) == 2
                or (len(x[0].split(".")) == 3 and is_agg_col(x[0]))
            )
            and (x[1] == FETCH_API.order.ASC or x[1] == FETCH_API.order.DESC)
            for x in order_by
        ), "expecting ['table.col', order] or ['agg.table.col', order]"

    # validate limit
    assert limit is None or (isinstance(limit, int) and limit > 0)

    # build up query
    base_query = "SELECT {fields} FROM {table} "
    join_query = "INNER JOIN {joined_table} ON {join_pair} "
    where_query = "WHERE {where_pairs} "
    group_query = "GROUP BY {group_cols} "
    order_query = "ORDER BY {order_cols} "
    limit_query = "LIMIT {limit_int} "

    # always build up base select query
    sql_base_query = SQL(base_query).format(
        fields=SQL(", ").join(
            [
                (
                    Composed(
                        [
                            SQL(get_agg_col_func(x)),
                            SQL("("),
                            Identifier(*(get_agg_col_name(x).split("."))),
                            SQL(")"),
                            SQL(" AS "),
                            Identifier(x),
                        ],
                    )
                    if is_agg_col(x)
                    else Composed(
                        [
                            Identifier(*(x.split("."))),
                            SQL(" AS "),
                            Identifier(x),
                        ],
                    )
                )
                for x in select_cols
            ],
        ),
        table=Identifier(table_name),
    )
    query = Composed(sql_base_query)

    # build join query if specified
    if join_tables is not None:
        join_table_names = [
            to_underscore(table_model.__name__) for table_model in join_tables
        ]

        for i, join_table_name in enumerate(join_table_names):
            sql_join_query = SQL(join_query).format(
                joined_table=Identifier(join_table_name),
                join_pair=Composed(
                    [
                        Identifier(*(join_on[i][0].split("."))),
                        SQL("="),
                        Identifier(*(join_on[i][1].split("."))),
                    ],
                ),
            )
            query += Composed([sql_join_query])

    # build up where query if specified
    if where_dict is not None:
        sql_where_query = SQL(where_query).format(
            where_pairs=(
                Composed(
                    [
                        SQL(" AND ").join(compose_all_where_possibilities(where_dict)),
                    ],
                )
            ),
        )
        query += Composed(sql_where_query)

    # build up group by query if specified
    if group_by is not None:
        sql_group_query = SQL(group_query).format(
            group_cols=SQL(", ").join(map(Identifier, group_by)),
        )
        query += Composed(sql_group_query)

    # build up order by query if specified
    if order_by is not None:
        sql_order_query = SQL(order_query).format(
            order_cols=SQL(", ").join(
                [
                    Composed(
                        [
                            Identifier(x[0]),
                            SQL(" "),
                            SQL(x[1]),
                        ],
                    )
                    for x in order_by
                ],
            ),
        )
        query += Composed(sql_order_query)

    # build up limit query if specified
    if limit is not None:
        sql_limit_query = SQL(limit_query).format(limit_int=Literal(limit))
        query += Composed(sql_limit_query)

    # execute query
    async with (
        get_async_pool().connection() as conn,
        conn.cursor(row_factory=dict_row) as cur,
    ):
        val_dict = format_val_dict(where_dict)

        logger.debug(f"query: {query.as_string(cur)}")
        logger.debug(f"vals: {val_dict}")

        await cur.execute(query, val_dict)

        records = await cur.fetchall()
        if not records:
            raise NoRecordsFoundError
        logger.debug(f"fetched rows {records}")

        # convert dict to model if all columns queried
        # all dict keys are in form of "table.col":val and
        # the model kwards wants "col":val
        if return_all:
            records = [
                from_table(**dh.remove_prefix_from_each_key(row)) for row in records
            ]
        return records


class FETCH_API:
    # static members
    all = "*"

    @dataclass(frozen=True)
    class order:
        ASC = "ASC"
        DESC = "DESC"

    @dataclass(frozen=True)
    class agg_funcs:
        AVG = "AVG"
        COUNT = "COUNT"
        MIN = "MIN"
        MAX = "MAX"
        SUM = "SUM"

    @dataclass(frozen=True)
    class where_operator:
        EQUAL = "="
        GREATER_THAN = ">"
        GREATER_THAN_OR_EQUAL_TO = ">="
        LESS_THAN = "<"
        LESS_THAN_OR_EQUAL_TO = "<="
        IN = "IN"
        BETWEEN = "BETWEEN"

    @staticmethod
    def make_agg_col(agg_func: str, col_name: str) -> str:
        assert any(
            agg_func in x for x in getmembers(FETCH_API.agg_funcs)
        ), f"not a valid agg func: {agg_func}"
        return f"{agg_func}.{col_name}"

    @staticmethod
    async def fetch_all(
        select_cols: list[str] | str,
        from_table: BaseModel,
        group_by: Optional[list[str]] = None,
        order_by: Optional[list[tuple[str, str]]] = None,
        limit: Optional[int] = None,
        flatten_return: bool = True,
    ) -> list[BaseModel]:
        """Fetch all rows from table

        -> returns a list of models or list of dicts
        """
        rows = await _fetch(
            select_cols=select_cols,
            from_table=from_table,
            join_tables=None,
            join_on=None,
            where_dict=None,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
        )

        return flatten(rows, select_cols) if flatten_return else rows

    @staticmethod
    async def fetch_where_uuid(
        select_cols: list[str] | str,
        from_table: BaseModel,
        where_uuid: UUID,
    ) -> BaseModel | dict:
        """Fetch rows where table.id==

        -> returns model or dict
        """
        rows = await _fetch(
            select_cols=select_cols,
            from_table=from_table,
            join_tables=None,
            join_on=None,
            where_dict={f"{to_underscore(from_table.__name__)}.id": where_uuid},
            group_by=None,
            order_by=None,
            limit=None,
        )

        assert len(rows) == 1
        return flatten(rows, select_cols)

    @staticmethod
    async def fetch_where_dict(
        select_cols: list[str] | str,
        from_table: BaseModel,
        where_dict: dict[str, tuple[str, Any]],
        group_by: Optional[list[str]] = None,
        order_by: Optional[list[tuple[str, str]]] = None,
        limit: Optional[int] = None,
        flatten_return: bool = True,
    ) -> BaseModel | dict:
        """Fetch rows where table.key==value in where_dict

        -> returns model or dict
        """
        rows = await _fetch(
            select_cols=select_cols,
            from_table=from_table,
            join_tables=None,
            join_on=None,
            where_dict=where_dict,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
        )

        return flatten(rows, select_cols) if flatten_return else rows

    @staticmethod
    async def fetch_join_where(
        select_cols: list[str] | str,
        from_table: BaseModel,
        join_tables: list[BaseModel] | BaseModel,
        join_on: list[tuple[str, str]] | tuple[str, str],
        where_dict: dict[str, tuple[str, Any]],
        group_by: Optional[list[str]] = None,
        order_by: Optional[list[tuple[str, str]]] = None,
        limit: Optional[int] = None,
        flatten_return: bool = True,
    ):
        """Fetch rows where table.key==value in where_dict
        Joins n tables with join_on

        -> returns model or dict
        """
        rows = await _fetch(
            select_cols=select_cols,
            from_table=from_table,
            join_tables=join_tables,
            join_on=join_on,
            where_dict=where_dict,
            group_by=group_by,
            order_by=order_by,
            limit=limit,
        )

        return flatten(rows, select_cols) if flatten_return else rows

    @staticmethod
    async def tg_fetch_where_uuids(
        select_cols: list[str] | str,
        from_table: BaseModel,
        where_uuids: list[UUID],
    ) -> list[BaseModel] | list[dict]:
        """ASYNC Task Group Multi Fetch"""
        assert isinstance(where_uuids, list)
        assert len(where_uuids) > 0
        assert isinstance(where_uuids[0], UUID)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    FETCH_API.fetch_where_uuid(
                        select_cols=select_cols,
                        from_table=from_table,
                        where_uuid=uuid,
                    ),
                )
                for uuid in where_uuids
            ]
        return [tsk.result() for tsk in tasks]

    @staticmethod
    async def tg_fetch_where_dicts(
        select_cols: list[str] | str,
        from_table: BaseModel,
        where_dicts: list[dict[str, tuple[str, Any]]],
        group_by: Optional[list[str]] = None,
        order_by: Optional[list[tuple[str, str]]] = None,
        limit: Optional[int] = None,
        flatten_return: bool = True,
    ) -> list[BaseModel] | list[dict]:
        """ASYNC Task Group Multi Fetch"""
        assert isinstance(where_dicts, list)
        assert len(where_dicts) > 0
        assert isinstance(where_dicts[0], dict)

        async with asyncio.TaskGroup() as tg:
            tasks = [
                tg.create_task(
                    FETCH_API.fetch_where_dict(
                        select_cols=select_cols,
                        from_table=from_table,
                        where_dict=where_dict,
                        group_by=group_by,
                        order_by=order_by,
                        limit=limit,
                        flatten_return=flatten_return,
                    ),
                )
                for where_dict in where_dicts
            ]
        return [tsk.result() for tsk in tasks]
