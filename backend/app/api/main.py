from fastapi import APIRouter

from backend.app.api.routes import devices, events, websocket

api_router = APIRouter()

api_router.include_router(devices.router)
api_router.include_router(events.router)
api_router.include_router(websocket.router)

@api_router.get("/")
async def root():
    """
        Check the health of the API
    """
    return {
        "message": "IoT Security Monitor API",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "devices": "/api/devices",
            "events": "/api/events",
            "websocket": "/ws",
        }
    }