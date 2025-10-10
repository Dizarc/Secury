from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select

from backend.app.core.database import engine, init_db, sessionDep
from backend.app import crud
from backend.app.models import (
    Device, DevicePublic, DeviceCreate, DeviceUpdate, DeviceStatus,
    Event, EventPublic, EventCreate, EventType
)

import json

# TODO: Change every get to the new way with the database.

# TODO: remove when you remove sensor_simulator()
import asyncio
import random

#TODO: Remove every print statement for production deployment and replace it with logging

#==========================================
# run before startup and yield after shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
        Runs when server starts
    """
    print("Starting server...")
    
    print("Initializing database...")
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

    print("Starting sensor simulation...")
    asyncio.create_task(sensor_simulator())

    yield

    print("Shutting down server...")

app = FastAPI(
    lifespan=lifespan,
    title="IoT Security Monitor API",
    description="Real-time home security monitoring system"
)

#==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

#==========================================
@app.get("/")
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

# TODO: Add device creation, update, deletion

#==========================================
@app.get("/api/devices", response_model=list[DevicePublic])
async def get_all_devices(session: sessionDep):
    """
        Get a list of all devices
    """
    devices = crud.get_devices(session=session)

    return devices

#==========================================
@app.get("/api/devices/{device_id}", response_model=DevicePublic)
async def get_device(device_id: int, session: sessionDep):
    """
        Get specific device by ID
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

#==========================================
@app.get("/api/devices/{device_id}/trigger", response_model=dict)
async def trigger_device(device_id: int, new_status: str, session: sessionDep):
    """
        Device state change for open/closed
        Will be called by the IoT devices
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if new_status not in DeviceStatus:
        raise HTTPException(status_code=404, detail="Status is invalid")
    
    device_in_update = DeviceUpdate(
        status=new_status, 
        last_updated=datetime.now(),
    )
    
    device = crud.update_device(session=session, db_device=device, new_device=device_in_update)

    # Change this to add the event into the database
    event = Event(
        device_id = device_id,
        type="status_change",
        details=f"status changed to {new_status}",
    )

    event = crud.create_event(session=session, event=event)

    return {
        "success": True,
        "device": DevicePublic.model_validate(device).model_dump(),
        "event": EventPublic.model_validate(event).model_dump(),
    }

#==========================================
@app.get("/api/events", response_model=list[EventPublic])
async def get_events(session: sessionDep, limit: int = 10):
    """
        Get recent events
    """
    events = crud.get_events(session=session, limit=limit)
    
    return events

#==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
        Websocket connection for real-time updates.
        Frontend will connect here to receive live sensor updates.
    """
    await manager.connect(websocket)
    print(f"New websocket connection. Total: {len(manager.active_connections)}")

    with Session(engine) as session:
        devices = crud.get_devices(session)
        events = crud.get_events(session, limit=10)

    await manager.send_personal_message({
        "type": "initial_state",
        "devices": [ DevicePublic.model_validate(device).model_dump() for device in devices],
        "events": [EventPublic.model_validate(event).model_dump() for event in events ],
    }, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            await manager.send_personal_message({
                "type": "ack",
                "message": "Message received",
            }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Websocket disconnected. Remaining: {len(manager.active_connections)}")

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
            new_status = random.choice([DeviceStatus.OPEN, DeviceStatus.CLOSED])

            if device.status != new_status:
                update_data = DeviceUpdate(status=new_status, last_updated=datetime.now())
                updated_device = crud.update_device(session=session, db_device=device, new_device=update_data)
                
                print(f"Sim: {device.name} changed to: {new_status.value}")

                event = Event(
                    device_id=device.id,
                    type= EventType.STATUS_CHANGE,
                    details=f"{device.name} changed to: {new_status.value}",
                )
                
                crud.create_event(session=session, event=event)

                await manager.broadcast({
                    "type": "device_update",
                    "device": DevicePublic.model_validate(updated_device).model_dump(),
                    "event": EventPublic.model_validate(event).model_dump(),
                })
