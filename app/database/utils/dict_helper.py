def add_prefix_to_each_key(
    input_dict: dict,
    prefix_to_add: str,
) -> dict:
    assert all(len(k.split(".")) == 1 for k in input_dict)
    return {f"{prefix_to_add}.{k}": v for k, v in input_dict.items()}


def remove_prefix_from_each_key(
    input_dict: dict,
) -> dict:
    assert all(len(k.split(".")) == 2 for k in input_dict)
    return {k.split(".")[1]: v for k, v in input_dict.items()}


def combine_dicts(
    dict_a: dict, dict_a_prefix: str, dict_b: dict, dict_b_prefix: str
) -> dict:
    assert dict_a_prefix != dict_b_prefix
    prefixed_dict_a = add_prefix_to_each_key(dict_a, dict_a_prefix)
    prefixed_dict_b = add_prefix_to_each_key(dict_b, dict_b_prefix)

    return prefixed_dict_a | prefixed_dict_b


def is_valid_dict(input_dict: dict) -> bool:
    return isinstance(input_dict, dict) and len(input_dict) > 0
