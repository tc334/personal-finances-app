import datetime
import json
import logging
from uuid import UUID

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

log = logging.getLogger(__name__)


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
    where_dict = {c_Journal.entity_id: entity_id}
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
            log.warning("The number of records returned exceeded the internal limit.")

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
