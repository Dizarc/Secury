from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from backend.app.main import app
from backend.app.api.deps import get_session
from backend.app.models import Device, DeviceStatus, User
from backend.app.core.security import get_password_hash

import pytest
import uuid 

@pytest.fixture(name="uuids", scope="module")
def test_uuids():
    uuids = {
        "window": uuid.uuid4(),
        "front_door": uuid.uuid4(),
        "back_door": uuid.uuid4(),
        "invalid": uuid.uuid4(),
        
    }
    yield uuids


@pytest.fixture(name="user", scope="session")
def test_user():
    user = {
        "email": "john@example.com", 
        "full_name": "John Doe", 
        "password": "password1"
    }
    yield user


@pytest.fixture(name="session", scope="function")
def session_fixture(uuids, user):
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
                id = uuids["window"],
                name = "Room Window",
                type = "Window",
                location = "Room 1",
                status = DeviceStatus.CLOSED,
                battery = 100,
            ),
            Device(
                id = uuids["front_door"],
                name = "Front door",
                type = "Door",
                location = "Main Entrance",
                status = DeviceStatus.CLOSED,
                battery = 75,
            ),
            Device(
                id = uuids["back_door"],
                name = "Back door",
                type = "Door",
                location = "Back Entrance",
                status = DeviceStatus.OPEN,
                battery = 50,
            ),
            User(
                email = user["email"], 
                full_name = user["full_name"], 
                hashed_password = get_password_hash(user["password"])
            )
        ])
        session.commit()

        yield session

@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session):
    """
        Provide a TestClient instance which
        simulates HTTP and websocket requestsfor FastAPI app
    """
    def get_session_override():
        yield session
    app.dependency_overrides[get_session] = get_session_override
    
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers", scope="function")
def auth_header_fixture(client, user):
    """
        Login to the user created in session_fixture
        retrieve the JWT token
        Return auth header
    """
    login_data = {
        "username": user["email"],
        "password": user["password"],
    }

    response = client.post("/api/login/access-token", data=login_data)

    assert response.status_code == 200

    token = response.json()["access_token"]

    return  {"Authorization": f"Bearer {token}"}



@pytest.fixture(name="auth_client", scope="function")
def auth_client_fixture(client, auth_headers):
    """
        Return a client that has JWT token already in headers
    """
    client.headers.update(auth_headers)

    return client