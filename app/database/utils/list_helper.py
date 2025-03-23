from typing import Any


def make_list(obj: list[Any] | Any):
    """
    if input is in form of list, return it
    else wrap it in a list
    """
    if obj is None or isinstance(obj, list):
        return obj
    return [obj]


def add_prefix_to_each_item(
    input_list: list,
    prefix_to_add: str,
) -> list:
    assert all(len(k.split(".")) == 1 for k in input_list)
    return [f"{prefix_to_add}.{k}" for k in input_list]


def remove_prefix_from_each_item(
    input_list: list,
) -> list:
    assert all(len(k.split(".")) == 2 for k in input_list)
    return [k.split(".")[1] for k in input_list]


def find_between_l_start_r_end(s, start, end) -> str:
    i_start = s.find(start) + len(start)
    i_end = s.rfind(end, i_start)
    return s[i_start:i_end]


def find_between_l_start_l_end(s, start, end) -> str:
    i_start = s.find(start) + len(start)
    i_end = s.find(end, i_start)
    return s[i_start:i_end]


def delete_between_l_start_l_end(s, start, end) -> tuple[str, int]:
    # loop and delete first instance of start
    # upto, including first instance of end
    n_deletes = 0
    while start in s and end in s:
        i_start = s.find(start)
        i_end = s.find(end, i_start)
        assert i_start < i_end
        s = s[:i_start] + s[i_end + 1 :]
        n_deletes += 1
    return s, n_deletes


def find_before_l_start(s, start) -> str:
    start = s.find(start)
    return s[0:start]


def is_valid_list(input_list: list) -> bool:
    return isinstance(input_list, list) and len(input_list) > 0
