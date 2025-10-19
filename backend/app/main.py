from contextlib import asynccontextmanager
from fastapi import FastAPI
from datetime import datetime
from sqlmodel import Session, select

from backend.app import crud
from backend.app.api.main import api_router
from backend.app.core.database import engine, init_db
from backend.app.core.websocket import manager, websocket_router
from backend.app.core.config import logger

from backend.app.models import (
    Device, DevicePublic, DeviceUpdate, DeviceStatus,
    EventPublic, EventCreate, EventType
)

# TODO: remove when you remove sensor_simulator()
import asyncio
import random

#==========================================
# run before startup and yield after shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Runs when server starts
    """
    logger.info("Starting server...")
    
    logger.info("Initializing database...")

    with Session(engine) as session:
        init_db(session)

        # If db is empty (TODO: Remove after)
        if not session.exec(select(Device)).first():
            session.add_all([
                Device(name="Room Window", type="window", location="Room 1"),
                Device(name="Front door", type="door", location="Main Entrance"),
                Device(name="Back door", type="door", location="Back Entrance"),
            ])
            session.commit()

    logger.info("Starting sensor simulation...")
    asyncio.create_task(sensor_simulator())

    logger.info("Starting healthchecking...")
    asyncio.create_task(monitor_device_health())
    yield

    logger.info("Shutting down server...")

#==========================================
async def monitor_device_health():
    """
        Check for offline devices every 2 minutes.
        Device should send heartbeat every 15 minutes.
        Wait 20 minutes before marking as offline.
    """
    while True:
        await asyncio.sleep(120)

        try:
            with Session(engine) as session:
                offline_devices = crud.check_offline_devices(session=session, timeout_minutes=20)

                for device in offline_devices:
                    logger.info(f"Device {device.name} is offline")

                    await manager.broadcast({
                        "type": "device_offline",
                        "device": DevicePublic.model_validate(device).model_dump(mode="json"),
                        "timestamp": datetime.now().isoformat(),
                    })
        except Exception as e:
            logger.error(f"Erorr in healthcheck: {e}")

#==========================================
# Simulate sensors (TODO: remove when real sensors are added)
async def sensor_simulator():
    """
        Simulate random sensor events
    """
    while True:
        await asyncio.sleep(5)

        with Session(engine) as session:
            devices = crud.get_devices(session=session)
            if not devices:
                continue

            # select random device and change its status
            device = random.choice(devices)
            new_status = random.choice([DeviceStatus.OPEN.value, DeviceStatus.CLOSED.value])

            if device.status != new_status:
                update_data = DeviceUpdate(status=new_status, last_updated=datetime.now())
                updated_device = crud.update_device(session=session, db_device=device, device_in=update_data)
                
                logger.info(f"Sim: {device.name} changed to: {new_status}")
                
                event = crud.create_event(
                    session=session, 
                    event=EventCreate(
                        device_id=device.id,
                        type= EventType.STATUS_CHANGE,
                        details=f"{device.name} changed to: {new_status}",
                    )
                )

                await manager.broadcast({
                    "type": "device_update",
                    "device": DevicePublic.model_validate(updated_device).model_dump(mode="json"),
                    "event": EventPublic.model_validate(event).model_dump(mode="json"),
                })

app = FastAPI(
    lifespan=lifespan,
    title="IoT Security Monitor API",
    description="Real-time home security monitoring system"
)

@app.get("/")
async def root():
    """
        Check the health of the API
    """
    
    logger.info("Root requested")

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

app.include_router(api_router, prefix="/api")
app.include_router(websocket_router)