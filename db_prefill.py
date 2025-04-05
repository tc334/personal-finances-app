from datetime import date

from app.database.psql_mgr.models.v1 import (
    m_Person,
    m_AccessLevels,
    m_Entity,
    m_PersonEntityJunction,
    m_Account,
    m_AccountType,
    m_Journal,
    m_Ledger,
    m_AccountActions,
)
from app.database.psql_mgr.api.insert import INSERT_API
from app.security.auth import get_password_hash


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
            name="T & A",
        )
    )

    await INSERT_API.insert_row(
        m_Entity(
            name="John & Jane Doe"
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

    income_summary = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Income Summary",
            type=m_AccountType.INCOME_SUMMARY,
        )
    )

    dividend = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Dividends (Master)",
            type=m_AccountType.DIVIDEND,
        )
    )

    return {
        "asset_long": a_long,
        "asset_short": a_short,
        "asset_owed": a_owed,
        "expense_operating": ex_operating,
        "expense_cogr": ex_cogr,
        "liability": liability,
        "equity": equity,
        "dividend": dividend,
        "income_summary": income_summary,
    }


async def add_accounts(master_dict, entity_id):
    ex_vehicles = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Vehicles - Expense",
            type=m_AccountType.EXPENSE,
            parent_account_id=master_dict["expense_operating"],
        )
    )

    ex_snowy = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Snowy",
            type=m_AccountType.EXPENSE,
            parent_account_id=ex_vehicles,
        )
    )

    ex_stormy = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Stormy",
            type=m_AccountType.EXPENSE,
            parent_account_id=ex_vehicles,
        )
    )

    a_bank = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Wells Fargo",
            type=m_AccountType.ASSET,
            parent_account_id=master_dict["asset_short"],
        )
    )

    a_vehicles = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Vehicles",
            type=m_AccountType.ASSET,
            parent_account_id=master_dict["asset_long"],
        )
    )

    eq_owners = await INSERT_API.insert_row_ret_uuid(
        m_Account(
            entity_id=entity_id,
            name="Owners Equity",
            type=m_AccountType.EQUITY,
            parent_account_id=master_dict["equity"],
        )
    )

    return a_bank, a_vehicles, eq_owners, ex_snowy


async def add_journal(user_id, entity_id, a_bank, a_vehicles, eq_owners, ex_snowy):
    ########################################################
    # Transaction 1
    ########################################################
    amount = 100000.0
    journal_1 = await INSERT_API.insert_row_ret_uuid(
        m_Journal(
            entity_id=entity_id,
            created_by=user_id,
            description="Owners put money into business",
            timestamp=date(year=2025, month=1, day=1),
        )
    )

    ledger_1_1 = await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_1,
            account_id=a_bank,
            amount=amount,
            direction=m_AccountActions.DEBIT,
        )
    )

    ledger_1_2 = await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_1,
            account_id=eq_owners,
            amount=amount,
            direction=m_AccountActions.CREDIT,
        )
    )

    ########################################################
    # Transaction 2
    ########################################################
    amount = 50000.0
    journal_2 = await INSERT_API.insert_row_ret_uuid(
        m_Journal(
            entity_id=entity_id,
            created_by=user_id,
            description="Business buys a vehicle",
            timestamp=date(year=2025, month=1, day=2),
        )
    )

    await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_2,
            account_id=a_bank,
            amount=amount,
            direction=m_AccountActions.CREDIT,
        )
    )

    await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_2,
            account_id=a_vehicles,
            amount=amount,
            direction=m_AccountActions.DEBIT,
        )
    )

    ########################################################
    # Transaction 3
    ########################################################
    amount = 5000.0
    journal_3 = await INSERT_API.insert_row_ret_uuid(
        m_Journal(
            entity_id=entity_id,
            created_by=user_id,
            description="Vehicle depreciates",
            timestamp=date(year=2025, month=1, day=3),
        )
    )

    await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_3,
            account_id=ex_snowy,
            amount=amount,
            direction=m_AccountActions.DEBIT,
        )
    )

    await INSERT_API.insert_row_ret_uuid(
        m_Ledger(
            journal_id=journal_3,
            account_id=a_vehicles,
            amount=amount,
            direction=m_AccountActions.CREDIT,
        )
    )


async def populate_infra():
    admin_id = await add_users()
    entity_id = await add_entities(admin_id)
    master_accounts = await add_master_accounts(entity_id)
    a_bank, a_vehicles, eq_owners, ex_snowy = await add_accounts(master_accounts, entity_id)
    await add_journal(admin_id, entity_id, a_bank, a_vehicles, eq_owners, ex_snowy)
