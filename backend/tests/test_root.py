def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "IoT Security Monitor API"
    assert data["status"] == "running"
    assert data["version"] == "1.0.0"

    assert "endpoints" in data
    assert "docs" in data["endpoints"]
    assert "devices" in data["endpoints"]
    assert "events" in data["endpoints"]
    assert "websocket" in data["endpoints"]

    assert data["endpoints"]["docs"] == "/docs"
    assert data["endpoints"]["devices"] == "/api/devices"
    assert data["endpoints"]["events"] == "/api/events"
    assert data["endpoints"]["websocket"] == "/ws"