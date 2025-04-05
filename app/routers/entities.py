import logging
from typing import Annotated
from uuid import UUID

import json
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status

from app.database.psql_mgr.models.v1 import m_Person, m_AccessLevels, c_Person, m_Entity, c_Entity, m_PersonEntityJunction, c_PersonEntityJunction
from app.database.psql_mgr.api.custom import CUSTOM_API
from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError
from app.database.psql_mgr.api.insert import INSERT_API
from ..dependencies import get_current_active_user
from app.security.auth import get_password_hash

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/entities",
    tags=["entities"],
)

ANNOTATED_USER = Annotated[m_Person, Depends(get_current_active_user)]


@router.get("/")
async def entities_get_all(current_user: ANNOTATED_USER) -> list[m_Entity]:
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all entities"
        )

    all_entities = await FETCH_API.fetch_all(
        select_cols=FETCH_API.all,
        from_table=m_Entity,
        order_by=[(c_Entity.created_on, FETCH_API.order.ASC)],
        flatten_return=False,
    )

    return all_entities


@router.get("/me")
async def entities_my_entities(current_user: ANNOTATED_USER) -> list[m_Entity]:
    try:
        my_entities = await FETCH_API.fetch_join_where(
            select_cols=FETCH_API.all,
            from_table=m_Entity,
            join_tables=[m_PersonEntityJunction],
            join_on=[(c_PersonEntityJunction.entity_id, c_Entity.id)],
            where_dict={
                c_PersonEntityJunction.user_id: current_user.id,
            },
            order_by=[(c_Entity.created_on, FETCH_API.order.ASC)],
            flatten_return=False,
        )

        return my_entities
    except NoRecordsFoundError:
        return []


@router.get("/users/{entity_id}")
async def entities_users(current_user: ANNOTATED_USER, entity_id: str) -> list[m_Person]:
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view user/entity relationships"
        )

    try:
        print(f"entity_id:{entity_id}")
        all_users = await FETCH_API.fetch_join_where(
            select_cols=FETCH_API.all,
            from_table=m_Person,
            join_tables=[m_PersonEntityJunction],
            join_on=(c_PersonEntityJunction.user_id, c_Person.id),
            where_dict={
                c_PersonEntityJunction.entity_id: entity_id,
            },
            order_by=[(c_Person.last_name, FETCH_API.order.ASC),
                      (c_Person.first_name, FETCH_API.order.ASC)],
            flatten_return=False,
        )

        return all_users
    except NoRecordsFoundError:
        return []


@router.post("/", status_code=201)
async def entity_add(
        current_user: ANNOTATED_USER,
        new_entity: m_Entity,
) -> m_Entity:
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add new entities"
        )

    # add new entity to DB
    try:
        new_entity = await INSERT_API.insert_row_ret_model(new_entity)
        logger.info(f"New entity {new_entity.name} added to DB.")
        return new_entity
    except Exception as e:
        print(e)
        logger.error(f"Error adding new {new_entity.name} to DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to add new entity to DB"
        )


@router.post("/add-user/{entity_id}/{user_id}", status_code=201)
async def entity_add_user(
        current_user: ANNOTATED_USER,
        entity_id: UUID,
        user_id: UUID,
) -> m_PersonEntityJunction:
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can join users and entities"
        )

    # add new entity to DB
    try:
        new_junc = await INSERT_API.insert_row_ret_model(
            m_PersonEntityJunction(
                entity_id=entity_id,
                user_id=user_id,
            )
        )
        logger.info(f"New user/entity junction added to DB.")
        return new_junc
    except Exception as e:
        print(e)
        logger.error(f"Error adding new user/entity junctions to DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to join user and entity in DB"
        )


@router.delete("/remove-user/{entity_id}/{user_id}", status_code=204)
async def entity_remove_user(
        current_user: ANNOTATED_USER,
        entity_id: UUID,
        user_id: UUID,
):
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete entities"
        )

    # remove users access from this entity in DB
    try:
        junc_id = await FETCH_API.fetch_where_dict(
            select_cols=c_PersonEntityJunction.id,
            from_table=m_PersonEntityJunction,
            where_dict={
                c_PersonEntityJunction.entity_id: entity_id,
                c_PersonEntityJunction.user_id: user_id,
            },
        )
        await CUSTOM_API.delete_row(m_PersonEntityJunction, junc_id)
        logger.info(f"User with id {user_id} removed from Entity with id {entity_id} in the DB.")

    except Exception as e:
        logger.error(f"Error removing user from entity in DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to delete entity from DB"
        )


@router.delete("/{entity_to_delete}", status_code=204)
async def user_delete(
        current_user: ANNOTATED_USER,
        entity_to_delete: str,
):
    # check for authorization
    if current_user.level != m_AccessLevels.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete entities"
        )

    # remover entity from DB
    try:
        await CUSTOM_API.delete_row(m_Entity, entity_to_delete)
        logger.info(f"Entity with id {entity_to_delete} deleted from DB.")

    except Exception as e:
        logger.error(f"Error removing entity with id {entity_to_delete} from DB. Exception{e}.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed trying to delete entity from DB"
        )


# TODO: edit entity
