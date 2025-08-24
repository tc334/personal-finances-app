import datetime
import logging
from uuid import UUID

from app.database.psql_mgr.api.insert import INSERT_API
from app.database.psql_mgr.api.custom import CUSTOM_API
from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError
from app.database.psql_mgr.models.v1 import (
    m_Account,
    c_Account,
    m_Ledger,
    c_Ledger,
    m_Journal,
    c_Journal,
    m_Person,
    c_Person,
)
from app.logic.accounts import BusinessLogicException

logger = logging.getLogger(__name__)


async def get_journal_entries(
        entity_id: UUID,
        max_rows: int,
        start_date: datetime.date,
        stop_date: datetime.date,
        account_name: str,
) -> list:

    # This is how I handle the user not providing a max_rows
    arbitrary_max = 10000
    if max_rows is None:
        limit = arbitrary_max
    else:
        limit = max_rows

    # Format the where_dict based on which constraints are specified by user
    where_dict = {
        c_Journal.entity_id: entity_id,
        c_Journal.valid: True,
    }
    if start_date is not None and stop_date is not None:
        where_dict[c_Journal.timestamp] = (FETCH_API.where_operator.BETWEEN, (start_date, stop_date))
    elif start_date is not None:
        where_dict[c_Journal.timestamp] = (FETCH_API.where_operator.GREATER_THAN, start_date)
    elif stop_date is not None:
        where_dict[c_Journal.timestamp] = (FETCH_API.where_operator.LESS_THAN, stop_date)

    if account_name is not None:
        where_dict[c_Account.name] = account_name

    # make DB call
    try:
        results = await FETCH_API.fetch_join_where(
            select_cols=[
                c_Journal.id,
                c_Journal.description,
                c_Journal.vendor,
                c_Journal.timestamp,
                c_Person.first_name,
                c_Person.last_name,
                c_Ledger.amount,
                c_Ledger.direction,
                c_Account.name,
            ],
            from_table=m_Journal,
            join_tables=[m_Ledger, m_Account, m_Person],
            join_on=[
                (c_Ledger.journal_id, c_Journal.id),
                (c_Ledger.account_id, c_Account.id),
                (c_Journal.created_by, c_Person.id),
            ],
            where_dict=where_dict,
            order_by=[(c_Journal.timestamp, FETCH_API.order.DESC)],
            limit=limit,
        )
        if len(results) == arbitrary_max:
            logger.warning("The number of records returned exceeded the internal limit.")

        # list of unique journal IDs sorted by date
        results_journal_only = sorted(list(set([(
            item[c_Journal.id],
            item[c_Journal.timestamp],
            item[c_Person.first_name] + " " + item[c_Person.last_name],
            item[c_Journal.vendor],
            item[c_Journal.description]
        ) for item in results])), key=(lambda x: x[1]), reverse=True)

        list_out = []
        for journal in results_journal_only:
            journal_id = journal[0]

            credits = [{"amount": str(item[c_Ledger.amount]), "account": item[c_Account.name]} for item in results if item[c_Journal.id] == journal_id and item[c_Ledger.direction] == "CREDIT"]
            debits = [{"amount": str(item[c_Ledger.amount]), "account": item[c_Account.name]} for item in results if item[c_Journal.id] == journal_id and item[c_Ledger.direction] == "DEBIT"]

            list_out.append({
                "date": journal[1].isoformat(),
                "user": journal[2],
                "vendor": journal[3],
                "description": journal[4],
                "credits": credits,
                "debits": debits,
            })

        return list_out

    except NoRecordsFoundError:
        raise BusinessLogicException("No matching journal entries found")


async def add_transaction(
        journal: m_Journal,
        ledger_list: list[m_Ledger],
) -> UUID:

    # check for ledger balance
    if not ledger_balance_check(ledger_list):
        raise BusinessLogicException("Ledger entries not balanced. ")

    # add new journal entry to DB
    try:
        journal_id = await INSERT_API.insert_row_ret_uuid(journal)
        logger.info(f"New journal entry {journal_id} added to DB.")
    except Exception as e:
        logger.error(f"Error adding new journal entry to DB. Exception {e}.")
        raise BusinessLogicException("Error adding transaction to DB.")

    # add all ledger rows to DB
    for ledger in ledger_list:
        # augment with journal id from above
        ledger.journal_id = journal_id
        try:
            ledger_id = await INSERT_API.insert_row_ret_uuid(ledger)
            logger.debug(f"New ledger entry {ledger_id} added to DB.")
        except Exception as e:
            logger.error(f"Error adding new ledger entry to DB. Exception {e}.")
            raise BusinessLogicException("Error adding transaction to DB.")

    # if you made it this far, the full transaction is valid. update valid col
    try:
        query_str = f"UPDATE journal SET valid = true WHERE id = '{journal_id}';"
        await CUSTOM_API.generic_query_no_return(query_str)
        return journal_id
    except Exception as e:
        logger.error(f"Error flipping journal valid flag to true. Exception {e}.")
        raise BusinessLogicException("Error adding transaction to DB.")


def ledger_balance_check(ledger_list: list[m_Ledger]):
    sum_debit = sum([ledger.amount for ledger in ledger_list if ledger.direction == 'DEBIT'])
    sum_credit = sum([ledger.amount for ledger in ledger_list if ledger.direction == 'CREDIT'])

    return True if sum_debit == sum_credit else False
