from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import List, Dict
from sqlmodel import Session

from backend.app.core.database import engine, init_db

import json

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

    print("Starting sensor simulation...")
    asyncio.create_task(sensor_simulator())

    yield
    print("Shutting down server...")
    print("Saving events to text file...")
    with open("events.txt", mode="w") as file:
        file.write(json.dumps(events))

app = FastAPI(
    lifespan=lifespan,
    title="IoT Security Monitor API",
    description="Real-time home security monitoring system"
)

#==========================================
# Store device information and event history (TODO: Change this later on)
devices: Dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Room Window",
        "type": "window",
        "location": "room 1",
        "status": "closed",
        "battery": 100,
        "last_updated": datetime.now().isoformat()
    },
    2: {
        "id": 2,
        "name": "Front Door",
        "type": "door",
        "location": "Entrance",
        "status": "closed",
        "battery": 100,
        "last_updated": datetime.now().isoformat()
    }
}

events: List[dict] = []

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
# Func to insert an event to events
def create_event(device_id: int, event_type: str, details: str):
    event = {
        "id": len(events) + 1,
        "device_id": device_id,
        "device_name": devices[device_id]["name"],
        "type" : event_type,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }

    events.append(event)

    return event

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
async def get_all_devices():
    """
        Get a list of all devices
    """
    return {
        "success": True,
        "count": len(devices),
        "devices": list(devices.values())
    }

#==========================================
@app.get("/api/devices/{device_id}")
async def get_device(device_id: int):
    """
        Get specific device by ID
    """
    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return { "success": True, "device": devices[device_id]}

#==========================================
@app.get("/api/devices/{device_id}/trigger")
async def trigger_device(device_id: int, new_status: str):
    """
        Device state change for open/closed
        Will be called by the IoT devices
    """

    if device_id not in devices:
        raise HTTPException(status_code=404, detail="Device not found")
    
    old_status = devices[device_id]["status"]
    devices[device_id]["status"] = new_status
    devices[device_id]["last_updated"] = datetime.now().isoformat()

    event = create_event(
        device_id,
        "status_change",
        f"status changed from {old_status} to {new_status}"
    )

    return {
        "success": True,
        "device": devices[device_id],
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
