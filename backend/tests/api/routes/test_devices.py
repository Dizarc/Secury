from backend.app.models import DeviceStatus, EventType

def test_get_all_devices(client):
    response = client.get("/api/devices")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    
    for device in data:
        assert "id" in device
        assert "name" in device
        assert "type" in device
        assert "location" in device
        assert "status" in device
        assert "battery" in device


def test_get_device_valid(client):
    response = client.get("/api/devices/1")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Room Window"
    assert data["type"] == "Window"
    assert data["location"] == "Room 1"
    assert data["status"] in DeviceStatus
    assert "battery" in data
    assert "last_updated" in data
    assert "last_seen" in data


def test_get_device_invalid(client):
    response = client.get("/api/devices/999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Device not found"


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