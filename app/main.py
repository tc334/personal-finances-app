from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database.utils.service_mgr import start_services, stop_services
from app.security.auth import login_for_access_token
from app.routers import users

app = FastAPI()

app.include_router(users.router)


@app.post("/token")
async def token_func(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    access_token = await login_for_access_token(form_data.username, form_data.password)
    return access_token


@app.on_event("startup")
async def startup_event():
    await start_services(app_name="FASTAPI")


@app.on_event("shutdown")
async def shutdown_event():
    await stop_services()
