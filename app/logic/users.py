from uuid import UUID

from app.database.psql_mgr.models.v1 import m_Person, m_PersonEntityJunction, c_PersonEntityJunction
from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError


class BusinessLogicException(Exception):
    pass


async def user_in_entity(user: m_Person, entity_id: UUID) -> bool:
    try:
        results = await FETCH_API.fetch_where_dict(
            select_cols=c_PersonEntityJunction.id,
            from_table=m_PersonEntityJunction,
            where_dict={
                c_PersonEntityJunction.entity_id: entity_id,
                c_PersonEntityJunction.user_id: user.id,
            },
        )
        if results and results is not None:
            return True
        else:
            return False

    except NoRecordsFoundError:
        return False
