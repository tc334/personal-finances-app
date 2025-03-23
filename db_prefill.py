from app.database.psql_mgr.models.v1 import m_Person, m_AccessLevels
from app.database.psql_mgr.api.insert import INSERT_API
from app.security.auth import get_password_hash


async def add_users():
    await INSERT_API.insert_row(
        m_Person(
            first_name="Tegan",
            last_name="Counts",
            email="foo@bar.com",
            level=m_AccessLevels.USER,
            active=True,
            hashed_password=get_password_hash("abc"),
        )
    )


async def populate_infra():
    await add_users()
