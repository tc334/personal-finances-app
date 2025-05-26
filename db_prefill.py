from datetime import date

from app.database.psql_mgr.models.v1 import (
    m_Person,
    m_AccessLevels,
    m_Entity,
    m_PersonEntityJunction,
    m_Account,
    c_Account,
    m_AccountType,
    m_Journal,
    m_Ledger,
    m_AccountActions,
)
from app.database.psql_mgr.api.insert import INSERT_API
from app.database.psql_mgr.api.fetch import FETCH_API
from app.security.auth import get_password_hash
from account_tree import tree as TREE
from sample_journal import journal as JOURNAL


async def add_users():
    admin_id = await INSERT_API.insert_row_ret_uuid(
        m_Person(
            email="foo@bar.com",
            hashed_password=get_password_hash("abc"),
            first_name="Tegan",
            last_name="Counts",
            level=m_AccessLevels.ADMIN,
            active=True,
            confirmed=True,
        )
    )

    return admin_id


async def add_entities(admin_id):
    entity_id = await INSERT_API.insert_row_ret_uuid(
        m_Entity(
            name="1982 Counts",
        )
    )

    await INSERT_API.insert_row(
        m_Entity(
            name="Dummy Entity"
        )
    )

    await INSERT_API.insert_row(
        m_PersonEntityJunction(
            entity_id=entity_id,
            user_id=admin_id,
        )
    )

    return entity_id


async def add_master_accounts(entity_id):
    a_long = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Long Term Assets (Master)",
            type=m_AccountType.ASSET,
        )
    )

    a_short = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Short Term Assets (Master)",
            type=m_AccountType.ASSET,
        )
    )

    a_owed = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Owed Assets (Master)",
            type=m_AccountType.ASSET,
        )
    )

    ex_operating = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Operating Expenses (Master)",
            type=m_AccountType.EXPENSE,
        )
    )

    ex_cogr = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="COGR Expenses (Master)",
            type=m_AccountType.EXPENSE,
        )
    )

    equity = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Equity (Master)",
            type=m_AccountType.EQUITY,
        )
    )

    liability = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Liabilities (Master)",
            type=m_AccountType.EQUITY,
        )
    )

    income = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Income (Master)",
            type=m_AccountType.INCOME,
        )
    )

    dividend = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Dividends (Master)",
            type=m_AccountType.DIVIDEND,
        )
    )

    income_summary = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Income Summary",
            type=m_AccountType.INCOME_SUMMARY,
        )
    )

    return {
        "assets_long": a_long,
        "assets_short": a_short,
        "assets_owed": a_owed,
        "expenses_operating": ex_operating,
        "expenses_cogr": ex_cogr,
        "liabilities": liability,
        "equity": equity,
        "income": income,
        "dividends": dividend,
        "income_summary": income_summary,
    }


async def add_one_account(entity_id, parent_id, acct_dict):
    parent_type = await FETCH_API.fetch_where_dict(
        select_cols=c_Account.type,
        from_table=m_Account,
        where_dict={c_Account.id: parent_id},
    )

    account_id = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name=acct_dict["name"],
            parent_account_id=parent_id,
            type=parent_type,
        )
    )

    if "children" in acct_dict and len(acct_dict["children"]) > 0:
        for child_acct in acct_dict["children"]:
            await add_one_account(entity_id, account_id, child_acct)


async def add_accounts(entity_id, master_dict, tree):
    for key in master_dict:
        for acct in tree[key]:
            await add_one_account(entity_id, master_dict[key], acct)


async def add_journal(user_id, entity_id, transaction_list):
    for transaction in transaction_list:
        journal_id = await INSERT_API.insert_row_ret_uuid(
            m_Journal(
                vendor=transaction["vendor"] if "vendor" in transaction else None,
                description=transaction["description"],
                timestamp=transaction["timestamp"],
                entity_id=entity_id,
                created_by=user_id,
            )
        )

        for credit in transaction["credits"]:
            credit_account_id = await FETCH_API.fetch_where_dict(
                select_cols=c_Account.id,
                from_table=m_Account,
                where_dict={c_Account.name: credit["account"]}
            )

            await INSERT_API.insert_row(
                m_Ledger(
                    journal_id=journal_id,
                    account_id=credit_account_id,
                    direction=m_AccountActions.CREDIT,
                    amount=credit["amount"],
                )
            )

        for debit in transaction["debits"]:
            debit_account_id = await FETCH_API.fetch_where_dict(
                select_cols=c_Account.id,
                from_table=m_Account,
                where_dict={c_Account.name: debit["account"]}
            )

            await INSERT_API.insert_row(
                m_Ledger(
                    journal_id=journal_id,
                    account_id=debit_account_id,
                    direction=m_AccountActions.DEBIT,
                    amount=debit["amount"]
                )
            )


async def populate_infra():
    admin_id = await add_users()
    entity_id = await add_entities(admin_id)
    master_accounts = await add_master_accounts(entity_id)
    await add_accounts(entity_id, master_accounts, TREE)
    await add_journal(admin_id, entity_id, JOURNAL)
