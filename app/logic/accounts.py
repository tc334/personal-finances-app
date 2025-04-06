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


class BusinessLogicException(Exception):
    pass


async def get_account_total(account_id: UUID) -> float:
    try:
        sum_credits = await FETCH_API.fetch_where_dict(
            select_cols=FETCH_API.make_agg_col(FETCH_API.agg_funcs.SUM, c_Ledger.amount),
            from_table=m_Ledger,
            where_dict={
                c_Ledger.account_id: account_id,
                c_Ledger.direction: m_AccountActions.CREDIT,
            }
        )
        if sum_credits is None:
            sum_credits = 0.0
    except NoRecordsFoundError:
        sum_credits = 0.0

    try:
        sum_debits = await FETCH_API.fetch_where_dict(
            select_cols=FETCH_API.make_agg_col(FETCH_API.agg_funcs.SUM, c_Ledger.amount),
            from_table=m_Ledger,
            where_dict={
                c_Ledger.account_id: account_id,
                c_Ledger.direction: m_AccountActions.DEBIT,
            }
        )
        if sum_debits is None:
            sum_debits = 0.0
    except NoRecordsFoundError:
        sum_debits = 0.0

    return sum_credits - sum_debits


async def get_name_from_id(account_id: UUID) -> str:
    try:
        account_name = await FETCH_API.fetch_where_dict(
            select_cols=c_Account.name,
            from_table=m_Account,
            where_dict={
                c_Account.id: account_id
            }
        )
        return account_name
    except NoRecordsFoundError:
        raise BusinessLogicException("Account not found")


async def get_tree_from_account(account_id: UUID) -> dict:
    name = await get_name_from_id(account_id)
    amount = await get_account_total(account_id)

    try:
        results = await FETCH_API.fetch_where_dict(
            select_cols=c_Account.id,
            from_table=m_Account,
            where_dict={
                c_Account.parent_account_id: account_id,
            },
            flatten_return=False,
        )
        child_ids = [r[c_Account.id] for r in results]
        children = []
        for child_id in child_ids:
            child = await get_tree_from_account(child_id)
            children.append(child)
            amount += child["amount"]
        return {
            "name": name,
            "amount": amount,
            "children": children,
        }
    except NoRecordsFoundError:
        return {
            "name": name,
            "amount": amount,
            "children": []
        }


async def get_tree_from_master(master_type_key: str):
    if master_type_key not in master_account_names:
        raise BusinessLogicException("Invalid master type key")

    try:
        account_id = await FETCH_API.fetch_where_dict(
            select_cols=c_Account.id,
            from_table=m_Account,
            where_dict={
                c_Account.name: master_account_names[master_type_key],
            },
        )
        tree = await get_tree_from_account(account_id)
        return tree

    except NoRecordsFoundError:
        raise BusinessLogicException("Couldn't find master account")
