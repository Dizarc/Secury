def test_get_all_devices(client):
    response = client.get("/api/devices")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "devices" in data
    assert isinstance(data["devices"], list)
    assert data["count"] == len(data["devices"])

def test_get_device_valid(client):
    response = client.get("/api/devices/1")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert "device" in data
    assert data["device"]["id"] == 1

def test_get_device_invalid(client):
    response = client.get("/api/devices/999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Device not found"