import logging
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import HTTPException, status
from passlib.context import CryptContext

from app.utils.env_mgr import get_env
from app.database.psql_mgr.models.v1 import m_Person, c_Person, m_Entity, c_Entity, m_PersonEntityJunction, c_PersonEntityJunction
from app.database.psql_mgr.api.fetch import FETCH_API, NoRecordsFoundError


ACCESS_TOKEN_EXPIRE_DAYS = 1
ALGORITHM = "HS256"

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(data: dict):
    to_encode = data.copy()

    expiration_date = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    # to_encode.update({"expiration_date": expiration_date.isoformat()})
    to_encode.update({"exp": expiration_date})

    env = get_env()
    encoded_jwt = jwt.encode(to_encode, env.SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def verify_token(token: str) -> m_Person:
    logger.debug("verify_token()")
    env = get_env()
    try:
        logger.debug(f"Decoding JWT")
        payload_dict = jwt.decode(token, env.SECRET_KEY, algorithms=[ALGORITHM])
        logger.debug(payload_dict)
    except jwt.ExpiredSignatureError:
        logger.warning(f"User rejected due to expired JWT")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Expired token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.exceptions.DecodeError:
        logger.warning(f"User rejected due to JWT decode error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # pull user from DB
    try:
        user: m_Person = await FETCH_API.fetch_where_uuid(
            select_cols=FETCH_API.all,
            from_table=m_Person,
            where_uuid=payload_dict["sub"],
        )
    except:
        logger.warning(f"No user found matching token with uuid {payload_dict['sub']}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification error, could not find user {payload_dict['sub']} in the DB",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not (user.active and user.confirmed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User {user.first_name} {user.last_name} is not active and confirmed",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def authenticate_user(username: str, password: str) -> m_Person | bool:
    # look for this user in the DB
    # in this application, username=email
    try:
        user: m_Person = await FETCH_API.fetch_where_dict(
            select_cols=FETCH_API.all,
            from_table=m_Person,
            where_dict={c_Person.email: username},
        )
    except:
        logger.warning("Authentication error trying to login. Couldn't find user in DB")
        return False

    if not (user.active and user.confirmed):
        logger.warning(f"Authentication error trying to login. User isn't active and has confirmed email")
        return False

    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication error trying to login. Wrong password for user {user.first_name} {user.last_name}")
        return False

    return user


def verify_password(plain_password, hashed_password):
    new_hash = get_password_hash(plain_password)
    if new_hash != hashed_password[:len(new_hash)]:
        return False
    else:
        return True


def get_password_hash(password):
    env = get_env()
    return pwd_context.hash(password, salt=env.PASSWORD_SALT)


async def login_for_access_token(username, password):
    user: m_Person = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # create JWT
    token = create_access_token(
        data={
            "sub": str(user.id),
            "level": str(user.level)
        }
    )

    # provide token
    return {
        "access_token": token,
        "token_type": "bearer",
    }


async def check_entity_permissions(user_id, entity_id):
    try:
        await FETCH_API.fetch_where_dict(
            select_cols=c_PersonEntityJunction.id,
            from_table=m_PersonEntityJunction,
            where_dict={
                c_PersonEntityJunction.entity_id: entity_id,
                c_PersonEntityJunction.user_id: user_id,
            }
        )

        # if you get here, it means something came back, which is pass
        return True
    except NoRecordsFoundError:
        return False
