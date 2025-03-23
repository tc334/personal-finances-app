from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.database.psql_mgr.models.v1 import m_Person, m_AccessLevels
from app.utils.security_helpers import authenticate_user, create_access_token, authenticate_token
from app.database.utils.service_mgr import start_services, stop_services

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await authenticate_token(token)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: Annotated[m_Person, Depends(get_current_user)]):
    if not current_user.active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.get("/users/me", response_model=m_Person)
async def read_items(current_user: Annotated[m_Person, Depends(get_current_active_user)]):
    return current_user


@app.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user: m_Person = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # create JWT
    token = create_access_token(
        data={
            "person_id": str(user.id),
            "person_level": user.level
        }
    )

    # provide token
    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.on_event("startup")
async def startup_event():
    await start_services(app_name="FASTAPI")


@app.on_event("shutdown")
async def shutdown_event():
    await stop_services()
