from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.security.auth import verify_token
from app.database.psql_mgr.models.v1 import m_Person

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # print(f"......get current user")
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await verify_token(token)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[m_Person, Depends(get_current_user)]):
    # print("......get_current_active_user")
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    # print(f"Current user {current_user.first_name} passed JWT authentication.")
    return current_user


