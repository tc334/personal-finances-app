import datetime
import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person
from ..dependencies import get_current_active_user
from app.security.auth import check_entity_permissions
from app.logic.accounts import BusinessLogicException
from app.logic.journal import get_journal_entries

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/journal",
    tags=["journal"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


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
