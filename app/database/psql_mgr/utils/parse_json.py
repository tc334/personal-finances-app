import json
from functools import partial
from uuid import UUID

from psycopg.types.json import Jsonb, set_json_dumps, set_json_loads


def is_valid_uuid(uuid_string):
    try:
        UUID(uuid_string)
        return True
    except ValueError:
        return False


class UUIDEncoder(json.JSONEncoder):
    """A JSON encoder which can dump UUID."""

    def default(self, o):
        if isinstance(o, UUID):
            # if the obj is uuid, we simply return the str of uuid
            return str(o)
        return super().default(o)


def uuid_decoder_object_hook(d: dict):
    """A JSON decoder which can recreate UUID."""
    ret_d = {}
    for k, v in d.items():
        if isinstance(v, str) and is_valid_uuid(v):
            v = UUID(v)  # noqa: PLW2901
        ret_d[k] = v
    return ret_d


def wrap_json_vals(d: dict) -> dict:
    ret_d = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = Jsonb(v)  # noqa: PLW2901
        ret_d[k] = v
    return ret_d


def set_json_serdes():
    # set global psycopg.jsonb dump encoding
    set_json_dumps(partial(json.dumps, cls=UUIDEncoder))

    # set global psycopg.jsonb dump decoding
    set_json_loads(partial(json.loads, object_hook=uuid_decoder_object_hook))
