from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session, select

from backend.app.core.database import engine, init_db, sessionDep
from backend.app import crud
from backend.app.models import Device, DeviceUpdate, Event

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
                Device(name="Front door", type="door", location="Entrance"),
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

    async def broadcast_to_clients(self, message: dict):
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
        "endpoints": {
            "docs": "/docs",
            "devices": "/api/devices",
            "events": "/api/events"
        }
    }

#==========================================
@app.get("/api/devices")
async def get_all_devices(session: sessionDep):
    """
        Get a list of all devices
    """
    devices = crud.get_devices(session=session)

    return {
        "success": True,
        "count": len(devices),
        "devices": devices
    }

#==========================================
@app.get("/api/devices/{device_id}")
async def get_device(device_id: int, session: sessionDep):
    """
        Get specific device by ID
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return { "success": True, "device": device}

#==========================================
@app.get("/api/devices/{device_id}/trigger")
async def trigger_device(device_id: int, new_status: str, session: sessionDep):
    """
        Device state change for open/closed
        Will be called by the IoT devices
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_in_update = DeviceUpdate(status=new_status, last_updated=datetime.now().isoformat())
    
    device = crud.update_device(session=session, db_device=device, new_device=device_in_update)

    # Change this to add the event into the database
    event = Event(
        device_id = device_id,
        type="status_change",
        details=f"status changed to {new_status}"
    )

    return {
        "success": True,
        "device": device,
        "event": event
    }

#==========================================
@app.get("/api/events")
async def get_events(limit: int = 10):
    """
        Get recent events
    """
    return {
        "success": True,
        "count": len(events),
        "events": events[-limit:]
    }

#==========================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
        Websocket connection for real-time updates.
        Frontend will connect here to receive live sensor updates.
    """

    await manager.connect(websocket)

    print(f"New websocket connection. Total: {len(manager.active_connections)}")

    await manager.send_personal_message({
        "type": "initial_state",
        "devices": list(devices.values()),
        "events": events[-10:]
    }, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from client: {data}")

            await manager.send_personal_message({
                "type": "ack",
                "message": "Message received"
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
        await asyncio.sleep(10)

        # select random device and change its status
        device_id = random.choice(list(devices.keys()))
        new_status = random.choice(["open", "closed"])

        if devices[device_id]["status"] != new_status:
            print(f"Simulator: {devices[device_id]["name"]} changed to: {new_status}")
            await trigger_device(device_id, new_status)
