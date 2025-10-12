from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.core.database import get_session
from app.models import Device, DeviceStatus

import pytest

@pytest.fixture(name="session", scope="function")
def session_fixture():
    """
        Create a new database for each test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args = {"check_same_thread": False},
        poolclass = StaticPool,
    )
    
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all([
            Device(
                id = 1,
                name = "Room Window",
                type = "Window",
                location = "Room 1",
                status = DeviceStatus.CLOSED,
                battery = 100,
            ),
            Device(
                id = 2,
                name = "Front door",
                type = "Door",
                location = "Main Entrance",
                status = DeviceStatus.CLOSED,
                battery = 75,
            ),
            Device(
                id = 3,
                name = "Back door",
                type = "Door",
                location = "Back Entrance",
                status = DeviceStatus.OPEN,
                battery = 50,
            )
        ])
        session.commit()

        yield session

@pytest.fixture(scope="module")
def client_fixture(session: Session):
    """
        Provide a TestClient instance which
        simulates HTTP and websocket requestsfor FastAPI app
    """
    app.dependency_overrides[get_session] = session
    
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()