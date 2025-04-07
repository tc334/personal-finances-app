import logging
from typing import Annotated
from uuid import UUID

import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person
from ..dependencies import get_current_active_user
from app.security.auth import check_entity_permissions
from app.logic.accounts import get_tree_from_master, BusinessLogicException, get_all_account_amounts

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


@router.get("/master")
async def accounts_get_tree(
        current_user: ANNOTATED_USER,
        master_type_key: str,
        entity_id: UUID
) -> dict:

    # First, make sure this user is allowed to access this entity
    if not await check_entity_permissions(current_user.id, entity_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user is not allowed to access this entity",
        )

    try:
        tree = await get_tree_from_master(master_type_key)
        return tree

    except BusinessLogicException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/amounts")
async def accounts_get_tree(
        current_user: ANNOTATED_USER,
        entity_id: UUID
) -> dict:

    # First, make sure this user is allowed to access this entity
    if not await check_entity_permissions(current_user.id, entity_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user is not allowed to access this entity",
        )

    try:
        # good opportunity for Redis
        tree = await get_all_account_amounts(entity_id)
        return tree

    except BusinessLogicException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
