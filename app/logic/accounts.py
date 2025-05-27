import json
from uuid import UUID

from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError
from app.database.psql_mgr.models.v1 import (
    m_Person,
    m_AccessLevels,
    c_Person,
    m_Entity,
    c_Entity,
    m_PersonEntityJunction,
    c_PersonEntityJunction,
    m_Account,
    c_Account,
    m_Ledger,
    c_Ledger,
    m_AccountActions,
    m_AccountType,
)


master_account_names = {
    "ASSET_LONG": "Long Term Assets (Master)",
    "ASSET_SHORT": "Short Term Assets (Master)",
    "ASSET_OWED": "Owed Assets (Master)",
    "EXPENSE_OPERATING": "Operating Expenses (Master)",
    "EXPENSE_COGR": "COGR Expenses (Master)",
    "EQUITY": "Equity (Master)",
    "INCOME": "Income (Master)",
    "LIABILITY": "Liabilities (Master)",
    "DIVIDENDS": "Dividends (Master)"
}

DEBIT_ACCOUNTS = [m_AccountType.ASSET, m_AccountType.EXPENSE, m_AccountType.DIVIDEND]
CREDIT_ACCOUNTS = [m_AccountType.EQUITY, m_AccountType.INCOME, m_AccountType.LIABILITY]


class BusinessLogicException(Exception):
    pass


def sign_scalar(account_type: str, transaction_direction: str) -> float:
    if account_type in DEBIT_ACCOUNTS:
        if transaction_direction == m_AccountActions.DEBIT:
            return 1.0
        else:
            return -1.0
    elif account_type in CREDIT_ACCOUNTS:
        if transaction_direction == m_AccountActions.CREDIT:
            return 1.0
        else:
            return -1.0
    else:
        raise BusinessLogicException("unrecognized account type")


async def get_tree_from_master(master_type_key: str):
    if master_type_key not in master_account_names:
        raise BusinessLogicException("Invalid master type key")

    try:
        results = await FETCH_API.fetch_where_dict(
            select_cols=[c_Account.id, c_Account.entity_id],
            from_table=m_Account,
            where_dict={
                c_Account.name: master_account_names[master_type_key],
            },
        )
        tree = await get_tree_from_account(results[c_Account.id], results[c_Account.entity_id])
        return tree

    except NoRecordsFoundError:
        raise BusinessLogicException("Couldn't find master account")


def tree_recursion(current_account, account_list):
    children_indices = [idx for (idx, account) in enumerate(account_list) if account[c_Account.parent_account_id] == current_account[c_Account.id]]
    children = [tree_recursion(account_list[child_idx], account_list) for child_idx in children_indices]
    return {
        "name": current_account[c_Account.name],
        "id": str(current_account[c_Account.id]),
        "children": children,
    }


async def get_tree_from_account(account_id: UUID, entity_id: UUID) -> dict:
    try:
        account_list = await FETCH_API.fetch_where_dict(
            select_cols=[c_Account.id, c_Account.name, c_Account.parent_account_id],
            from_table=m_Account,
            where_dict={c_Account.entity_id: entity_id},
            order_by=[(c_Account.name, FETCH_API.order.ASC)],
        )
    except NoRecordsFoundError:
        raise BusinessLogicException("No accounts found associated with your entity")

    head_account = next((account for account in account_list if account[c_Account.id] == account_id), None)
    if head_account is None:
        raise BusinessLogicException("Could not find the account to make tree for")

    tree = tree_recursion(head_account, account_list)
    return tree


async def get_all_account_amounts(entity_id: UUID) -> dict[str, float]:
    results = await FETCH_API.fetch_join_where(
        select_cols=[c_Account.id, c_Account.type, c_Ledger.direction, FETCH_API.make_agg_col(FETCH_API.agg_funcs.SUM, c_Ledger.amount)],
        from_table=m_Ledger,
        join_tables=[m_Account],
        join_on=(c_Account.id, c_Ledger.account_id),
        where_dict={c_Account.entity_id: entity_id},
        group_by=[c_Account.id, c_Account.type, c_Ledger.direction],
        order_by=[(c_Account.id, FETCH_API.order.ASC),
                  (c_Ledger.direction, FETCH_API.order.ASC)],
    )
    d = {}
    key1 = 'SUM.ledger.amount'
    for item in results:
        key = str(item[c_Account.id])
        amount = sign_scalar(item[c_Account.type], item[c_Ledger.direction]) * float(item[key1])
        if key in d:
            d[key] += amount
        else:
            d[key] = amount
    return d


async def get_list_from_entity(entity_id: UUID) -> list[str]:
    try:
        results = await FETCH_API.fetch_where_dict(
            select_cols=c_Account.name,
            from_table=m_Account,
            where_dict={c_Account.entity_id: entity_id},
            flatten_return=True,
        )
        return results

    except NoRecordsFoundError:
        raise BusinessLogicException(f"No accounts found matching entity id {entity_id}")
