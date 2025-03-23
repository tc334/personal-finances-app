def check_return_all(return_cols) -> bool:
    return len(return_cols) == 1 and return_cols[0] == "*"
