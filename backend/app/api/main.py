from fastapi import APIRouter

from backend.app.api.routes import devices, events
from backend.app.core import websocket

api_router = APIRouter()

api_router.include_router(devices.router)
api_router.include_router(events.router)