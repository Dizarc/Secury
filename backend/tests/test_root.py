def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "IoT Security Monitor API"
    assert data["status"] == "running"
    assert "devices" in data["endpoints"]
    assert "events" in data["endpoints"]