def test_trigger_valid_device(client):
    response = client.get("/api/devices/1/trigger?new_status=open")
    assert response.status_code == 200

    data = response.json()
    assert data["success"] is True
    assert data["device"]["status"] in ["open", "closed"]
    assert "event" in data
    assert data["event"]["type"] == "status_change"

def  test_trigger_invalid_device(client):
    response = client.get("/api/devices/999/trigger?new_status=open")
    assert response.status_code == 404

    data = response.json()
    
    assert data["detail"] == "Device not found"