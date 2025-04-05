from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

from app.database.utils.service_mgr import start_services, stop_services
from app.security.auth import login_for_access_token
from app.routers import users, entities

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(entities.router)


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


@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request, exc):
    print(f"ALPHA:{exc.errors()}")
    return JSONResponse(
        status_code=400,
        content={"message": "Response validation error", "details": exc.errors()},
    )