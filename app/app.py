from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.db import create_db_and_tables
from app.schemas import UserCreate, UserRead, UserUpdate
from app.users import auth_backend, fastapi_users
from app.routes import router
from app.core.config import Settings

# Load settings from .env file
settings = Settings()

# Create FastAPI instance
app = FastAPI(
    title=settings.app_name, 
    description=settings.app_description,
    version=settings.app_version
)

# Mount assets
app.mount("/assets", StaticFiles(directory="app/assets"), name="assets")

# Include fastapi_users routes
app.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Include application routes
app.include_router(
    router,
    tags=["application"],
)


@app.on_event("startup")
async def on_startup():
    # Not needed if you setup a migration system like Alembic
    await create_db_and_tables()