from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from backend.app import crud
from backend.app.models import DevicePublic, EventPublic
from backend.app.core.database import engine
from backend.app.core.config import logger
from backend.app.api.deps import tokenDep

websocket_router = APIRouter(prefix="/ws", tags=["websocket"])

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
                logger.error(f"Error sending message: {e}")
                self.disconnect(connection)

manager = ConnectionManager()

@websocket_router.websocket("")
async def websocket_endpoint(websocket: WebSocket, token: tokenDep):
    """
        Websocket connection for real-time updates.
        Frontend will connect here to receive live sensor updates.
    """
    await manager.connect(websocket)
    
    logger.info(f"New websocket connection. Total: {len(manager.active_connections)}")

    with Session(engine) as session:
        devices = crud.get_devices(session=session)
        events = crud.get_events(session=session, limit=10)

    await manager.send_personal_message({
        "type": "initial_state",
        "devices": [ DevicePublic.model_validate(device).model_dump(mode="json") for device in devices],
        "events": [EventPublic.model_validate(event).model_dump(mode="json") for event in events],
    }, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")

            await manager.send_personal_message({
                "type": "ack",
                "message": "Message received",
            }, websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"Websocket disconnected. Remaining: {len(manager.active_connections)}")
