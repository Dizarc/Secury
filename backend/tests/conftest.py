from fastapi.testclient import TestClient
from app.main import app

import pytest

@pytest.fixture(scope="module")
def client():
    """
        Provide a TestClient instance which
        simulates HTTP and websocket requestsfor FastAPI app
    """
    with TestClient(app) as c:
        yield c