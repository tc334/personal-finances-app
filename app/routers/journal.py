import datetime
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person, m_Journal, m_Ledger
from ..dependencies import get_current_active_user
from app.security.auth import check_entity_permissions
from app.logic.accounts import BusinessLogicException
from app.logic.journal import get_journal_entries, add_transaction
from app.logic.users import user_in_entity

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/journal",
    tags=["journal"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


@router.post("/", status_code=201)
async def add_journal_entry(
        current_user: ANNOTATED_USER,
        new_journal_entry: m_Journal,
        ledger_list: list[m_Ledger],
) -> UUID:
    # check for authorization: user must be part of entity specified in journal entry
    if not await user_in_entity(current_user, new_journal_entry.entity_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user submitting the journal post is not part of the entity specified in the post content"
        )

    # add new entity to DB
    try:
        new_journal_entry.created_by = current_user.id
        return await add_transaction(new_journal_entry, ledger_list)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to add new entity to DB"
        )


@router.get("/")
async def get_journal(
        current_user: ANNOTATED_USER,
        entity_id: UUID,
        max_rows: int = None,
        start_date: datetime.date = None,
        stop_date: datetime.date = None,
        account_name: str = None,
) -> dict:
    # First, make sure this user is allowed to access this entity
    if not await check_entity_permissions(current_user.id, entity_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user is not allowed to access this entity",
        )

    try:
        entries = await get_journal_entries(entity_id, max_rows, start_date, stop_date, account_name)
        return {
            "journal_entries": entries,
        }

    except BusinessLogicException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )