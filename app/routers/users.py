import logging
from typing import Annotated
from uuid import UUID

import json

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person, m_AccessLevels, c_Person
from app.database.psql_mgr.api.custom import CUSTOM_API
from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError
from app.database.psql_mgr.api.insert import INSERT_API
from ..dependencies import get_current_active_user
from app.security.auth import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


@router.get("/me", response_model=m_Person)
async def read_items(current_user: ANNOTATED_USER):
    return current_user


@router.get("/")
async def user_get_all(current_user: ANNOTATED_USER) -> list[m_Person]:
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all users"
        )

    all_users = await FETCH_API.fetch_all(
        select_cols=FETCH_API.all,
        from_table=m_Person,
        order_by=[(c_Person.level, FETCH_API.order.ASC),
                  (c_Person.last_name, FETCH_API.order.ASC),
                  (c_Person.first_name, FETCH_API.order.ASC),],
        flatten_return=False,
    )

    return all_users


@router.get("/active")
async def user_active(current_user: ANNOTATED_USER) -> list[m_Person]:
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all users"
        )

    users = await FETCH_API.fetch_where_dict(
        select_cols=FETCH_API.all,
        from_table=m_Person,
        where_dict={
            c_Person.active: True,
            c_Person.confirmed: True,
        },
        order_by=[(c_Person.last_name, FETCH_API.order.ASC),
                  (c_Person.first_name, FETCH_API.order.ASC),],
        flatten_return=False,
    )

    return users


@router.post("/", status_code=201)
async def user_add(
        current_user: ANNOTATED_USER,
        new_user: m_Person,
) -> m_Person:
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add new users"
        )

    # check for duplicate email address
    if await email_exists(new_user.email):
        logger.error(f"When attempting to add new user {new_user.first_name} {new_user.last_name} with email"
                     f"{new_user.email}, an existing user is already in the DB with this email. Aborting new user add.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an existing user with this email"
        )
    else:
        logger.info(f"No existing email found for candidate new user {new_user.email}. Proceed with creating new user")

    # add new user to DB
    try:
        new_user = await INSERT_API.insert_row_ret_model(new_user)
        logger.info(f"New user {new_user.first_name} {new_user.last_name} added to DB.")
        return new_user
    except Exception as e:
        print(e)
        logger.error(f"Error adding new user {new_user.first_name} {new_user.last_name} to DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to add new user to DB"
        )


@router.delete("/{user_to_delete}", status_code=204)
async def user_delete(
        current_user: ANNOTATED_USER,
        user_to_delete: str,
):
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add new users"
        )

    # remover user from DB
    try:
        await CUSTOM_API.delete_row(m_Person, user_to_delete)
        logger.info(f"User with id {user_to_delete} deleted from DB.")

    except Exception as e:
        logger.error(f"Error removing new user with id {user_to_delete} from DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to delete user from DB"
        )

# TODO: edit user


async def email_exists(email: str) -> bool:
    try:
        await FETCH_API.fetch_where_dict(
            select_cols=c_Person.email,
            from_table=m_Person,
            where_dict={
                c_Person.email: email,
            }
        )
        return True

    except NoRecordsFoundError:
        return False
