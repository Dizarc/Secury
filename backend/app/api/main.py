from fastapi import APIRouter

from backend.app.api.routes import devices, events, login

api_router = APIRouter()

api_router.include_router(devices.router)
api_router.include_router(events.router)
api_router.include_router(login.router)