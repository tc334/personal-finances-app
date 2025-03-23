from datetime import datetime, timedelta, timezone
from copy import deepcopy
import logging

import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ValidationError

from app.utils.env_mgr import get_env
from app.database.psql_mgr.api.fetch import FETCH_API
from app.database.psql_mgr.models.v1 import m_Person, c_Person


logger = logging.getLogger(__name__)
ACCESS_TOKEN_EXPIRE_DAYS = 0.003
ALGORITHM = "HS256"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    inner_data: dict
    expiration_date: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    new_hash = get_password_hash(plain_password)
    if new_hash != hashed_password[:len(new_hash)]:
        return False
    else:
        return True


def get_password_hash(password):
    env = get_env()
    return pwd_context.hash(password, salt='a9l1wVbjecqw43bP6kDhsO')


def create_access_token(data: dict):
    expiration_date = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    token_data = TokenData(
        inner_data=data,
        expiration_date=expiration_date.isoformat(),
    )
    payload_dict = dict(deepcopy(token_data))

    env = get_env()
    encoded_jwt = jwt.encode(payload_dict, env.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_token(token: str) -> TokenData | bool:
    env = get_env()
    try:
        payload_dict = jwt.decode(token, env.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.exceptions.DecodeError:
        logger.error("Invalid JWT")
        return False
    try:
        token_data = TokenData(**payload_dict)
    except ValidationError:
        logger.error("JWT missing TokenData")
        return False
    return token_data


async def authenticate_token(token: str) -> m_Person | bool:
    token_data = decode_token(token)
    if not token_data:
        return False

    # check date
    expiration_date = datetime.fromisoformat(token_data.expiration_date)
    if expiration_date < datetime.now(timezone.utc):
        logger.warning("JWT Expired")
        logger.warning(f"       now:{datetime.now(timezone.utc)}")
        logger.warning(f"expiration:{expiration_date}")
        return False

    # pull
    try:
        user: m_Person = await FETCH_API.fetch_where_uuid(
            select_cols=FETCH_API.all,
            from_table=m_Person,
            where_uuid=token_data.inner_data["person_id"],
        )
        return user
    except:
        logger.warning("No user found matching token")
        return False


async def authenticate_user(username: str, password: str) -> m_Person | bool:
    # look for this user in the DB
    # in this application, username=email
    try:
        print(f"username:{username}")
        user: m_Person = await FETCH_API.fetch_where_dict(
            select_cols=FETCH_API.all,
            from_table=m_Person,
            where_dict={c_Person.email: username},
        )
    except:
        logger.warning("Authentication error trying to login. Couldn't find user in DB")
        return False

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication error trying to login. Wrong password for user {user.first_name} {user.last_name}")
        return False

    return user
