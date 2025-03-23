import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person, m_AccessLevels, c_Person
from app.database.psql_mgr.api.fetch import FETCH_API
from app.database.psql_mgr.api.insert import INSERT_API
from ..dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


@router.get("/me", response_model=m_Person)
async def read_items(current_user: ANNOTATED_USER):
    return current_user


@router.get("/get_all")
async def user_get_all(current_user: ANNOTATED_USER) -> list[m_Person]:
    all_users = await FETCH_API.fetch_all(
        select_cols=FETCH_API.all,
        from_table=m_Person,
        order_by=[(c_Person.level, FETCH_API.order.ASC),],
    )
    return all_users


@router.post("/add")
async def user_add(
        current_user: ANNOTATED_USER,
        new_user: m_Person,
) -> str:
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add new users"
        )

    try:
        # TODO: add password hash into model
        new_uuid: UUID = await INSERT_API.insert_row_ret_uuid(new_user)
        return str(new_uuid)
    except:
        logger.error("Error adding new user. Unknown DB insert error.")
        logger.error(f"new_user:{new_user}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to add new user to DB"
        )

# TODO: delete user
# TODO: edit user
