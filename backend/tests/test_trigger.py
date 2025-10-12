from app.models import DeviceStatus, EventType
def test_trigger_valid_device(client):
    response = client.get("/api/devices/1/trigger?new_status=open")
    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "device" in data
    assert "event" in data

    assert data["device"]["status"] == DeviceStatus.OPEN.value
    assert data["device"]["id"] == 1

    assert data["event"]["type"] == EventType.STATUS_CHANGE.value
    assert data["event"]["device_id"] == 1

def  test_trigger_invalid_device(client):
    response = client.get("/api/devices/999/trigger?new_status=open")
    assert response.status_code == 404

    data = response.json()
    
    assert data["detail"] == "Device not found"