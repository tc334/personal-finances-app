import logging
from collections import OrderedDict
from datetime import datetime, date
from enum import Enum
from importlib import import_module
from inspect import getmembers, isclass
from os.path import dirname
from pathlib import Path
from pprint import pformat
from types import ModuleType
from uuid import UUID

from pydantic import BaseModel

from app.database.utils import list_helper as lh
from app.database.psql_mgr.psql_mgr import get_schema_version

logger = logging.getLogger(__name__)

SQL_TYPES = {
    "BOOLEAN": bool,
    "CHAR": str,
    "VARCHAR": str,
    "TEXT": str,
    "NUMERIC": float,
    "REAL": float,
    "INTEGER": int,
    "INT": int,
    "SMALLINT": int,
    "BIGINT": int,
    "DECIMAL": float,
    "FLOAT": float,
    "SERIAL": int,
    "TIMESTAMP": datetime,
    "DATE": date,
    "UUID": UUID,
    "JSON": dict,
    "JSONB": dict,
    "BYTEA": bytes,
}
assert len(set(SQL_TYPES.keys())) == len(SQL_TYPES.keys())

SQL_CONSTRAINTS = ["PRIMARY", "FOREIGN", "CHECK", "UNIQUE", "CONSTRAINT"]
assert len(set(SQL_CONSTRAINTS)) == len(SQL_CONSTRAINTS)


def read_schema_into_dict(schema_module: ModuleType) -> tuple[dict, dict]:
    enums = OrderedDict()
    tables = OrderedDict()

    """read and execute the schema file"""
    assert schema_module.__file__ is not None
    schema_path = Path(dirname(schema_module.__file__), f"{get_schema_version()}.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    logger.info(f"read in {schema_path}, len={len(sql)}")

    # remove all comments. Will start with "--" and go to \n
    sql, n_deletes = lh.delete_between_l_start_l_end(sql, "--", "\n")
    logger.info(f"removed {n_deletes} comments")

    # commands will always end with ";"
    # strip whitespace from start and end of command
    commands = [c.strip() for c in sql.split(";")]

    # very last command will be empty, due to split on last ";"
    assert len(commands[-1]) == 0
    commands = commands[0:-1]
    logger.info(f"schema file has {len(commands)} commands")

    # get all enums first
    non_enum_commands: list[str] = []
    for command in commands:
        # create enum
        if command.split()[:2] == ["create", "type"]:
            enum_name = command.split()[2]
            enum_name = enum_name[:-1] if enum_name.endswith("(") else enum_name
            assert enum_name == enum_name.lower(), "enum names must be lowercase"
            attrs = []
            for val in lh.find_between_l_start_r_end(command, "(", ")").split(","):
                enum_field = val.strip().strip("'").strip('"')
                assert enum_field == enum_field.upper(), "enum fields must be uppercase"
                attrs.append(enum_field)
            enums[enum_name] = attrs
        else:
            non_enum_commands.append(command)
    # force enums to be unique names
    assert len(set(enums.keys())) == len(enums.keys())
    logger.info(f"finished reading in {len(enums)} enums")

    # now re-loop with user defined enum types known - to create tables
    for command in non_enum_commands:
        # create table
        if command.split()[:2] == ["create", "table"]:
            table_name = command.split()[2]
            # check that schema does not have space btw tablename and "("
            table_name = table_name[:-1] if table_name.endswith("(") else table_name
            assert table_name == table_name.lower(), "tablename must be lowercase"
            attrs = []
            table_commands = lh.find_between_l_start_r_end(command, "(", ")")
            # delete all params in commands - btw () - helps parsing
            table_commands, n_deletes = lh.delete_between_l_start_l_end(
                table_commands, "(", ")"
            )
            logger.debug(f"{table_name} deleted {n_deletes} functions")
            # split commands nicely on ","
            table_commands = [c.strip() for c in table_commands.split(",")]

            debug_skipped_lines = []
            for line in table_commands:
                words = line.split()  # split on whitespace
                assert len(words) > 0

                # check if line is a constraint not column creation
                if words[0] in SQL_CONSTRAINTS:
                    debug_skipped_lines.append(line)
                    continue

                # if column, it should have a valid type
                col_name = words[0]
                col_type = words[1]
                assert (
                    col_name == col_name.lower()
                ), f"col {col_name}; column names must be lowercase"
                assert (
                    col_type == col_type.upper() or col_type in enums
                ), f"col {col_type}; column types must be uppercase or enum"

                # check for array of type
                is_array = col_type.endswith("[]")
                if is_array:
                    # trim array off
                    col_type, n = lh.delete_between_l_start_l_end(col_type, "[", "]")
                    assert n == 1, "expected to only trim one set of brackets"

                # check for default specified
                is_optional = False
                if "DEFAULT" in [w.upper() for w in words] or "NOT NULL" not in [
                    words[i_w].upper() + " " + words[i_w + 1].upper()
                    for i_w in range(len(words) - 1)
                ]:
                    is_optional = True

                # it should be a custom (enum) type or normal sql type
                assert col_type in SQL_TYPES or col_type in enums, "must be in one"
                assert not (col_type in SQL_TYPES and col_type in enums), "one or other"
                t = (
                    SQL_TYPES[col_type].__name__
                    if col_type in SQL_TYPES
                    else f"m_{to_cc(col_type)}"
                )
                if is_array:
                    t = f"list[{t}]"
                if is_optional:
                    t = f"Optional[{t}] = None"

                attrs.append((col_name, t))

            tables[table_name] = attrs
            if len(debug_skipped_lines) > 0:
                logger.debug(f"{table_name} skipped lines: {debug_skipped_lines}")

        # all other commands
        else:
            logger.debug(f"non table/enum command in schema file {command}")

    logger.info(f"schema file has {len(tables)} tables")

    logger.debug(f"enums: {pformat(enums)}")
    logger.debug(f"tables: {pformat(tables)}")

    return enums, tables


def read_models_into_dict(models_module: ModuleType):
    imported_models = import_module(f"{models_module.__name__}.{get_schema_version()}")

    # loop over every class/enum in models file
    all_classes = OrderedDict()
    for name, obj in getmembers(imported_models):
        attr = []
        if (
            isclass(obj)
            and obj not in (BaseModel, Enum)
            and (issubclass(obj, (BaseModel, Enum)))
        ):
            # enums
            if issubclass(obj, Enum):
                attr = [k.value for k in getattr(imported_models, name)]
            # pydantic classes
            else:
                attr = list(getattr(imported_models, name).model_fields.keys())

            all_classes[name] = attr

    return all_classes


def to_cc(underscore_name: str) -> str:
    cc_name = ""

    # start by cap first letter
    next_is_cap = True
    for char in underscore_name:
        assert not (
            next_is_cap and char == "_"
        ), "cant have 2 __ in a row, or start with _"

        if next_is_cap:
            cc_name += char.upper()
            next_is_cap = False
        elif char == "_":
            next_is_cap = True
            continue
        else:
            cc_name += char

    return cc_name


def to_underscore(model_name: str) -> str:
    assert model_name[:2] == "m_"
    assert model_name[2] == model_name[2].upper()
    # trim start of string
    model_name = model_name[2:]

    table_name = ""
    for i, char in enumerate(model_name):
        if i == 0:
            table_name += char.lower()
        elif char == char.upper():
            table_name += "_" + char.lower()
        else:
            table_name += char
    return table_name


def write_dict_to_models_and_cols(
    enums: dict[str, list[str]],
    tables: dict[str, list[tuple[str, str]]],
    model_module: ModuleType,
) -> None:
    assert model_module.__file__ is not None
    model_path = Path(dirname(model_module.__file__), f"{get_schema_version()}.py")
    with open(model_path, "w", encoding="utf-8") as f:
        # all one time adds
        f.write("# pylint: disable=too-many-lines\n")
        f.write("from dataclasses import dataclass\n")
        f.write("from datetime import datetime, date\n")
        if len(enums) > 0:
            f.write("from enum import Enum\n")
        f.write("from typing import Optional\n")
        f.write("from uuid import UUID\n")

        f.write("\n")
        f.write("from pydantic import BaseModel\n")

        f.write("\n")
        f.write('""" This class is autogenerated """\n')

        # add enums
        for k, v in enums.items():
            # model
            f.write("\n\n")
            f.write(f"class m_{to_cc(k)}(str, Enum):\n")
            for i in v:
                f.write(f'    {i} = "{i}"\n')

        # add tables
        for k, v in tables.items():
            # model
            f.write("\n\n")
            f.write(f"class m_{to_cc(k)}(BaseModel):\n")
            for i in v:
                f.write(f"    {i[0]}: {i[1]}\n")

        for k, v in enums.items():
            # column
            f.write("\n\n")
            f.write("@dataclass(frozen=True)\n")
            f.write(f"class c_{to_cc(k)}:\n")
            for i in v:
                f.write(f'    {i} = "{i}"\n')

        for k, v in tables.items():
            # column
            f.write("\n\n")
            f.write("@dataclass(frozen=True)\n")
            f.write(f"class c_{to_cc(k)}:\n")
            for i in v:
                f.write(f'    {i[0]} = "{k}.{i[0]}"\n')
