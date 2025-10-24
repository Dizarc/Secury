from backend.app.models import DeviceStatus, EventType, DeviceCreate, DeviceUpdate

from datetime import datetime

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


def test_create_device(client):
    new_device = DeviceCreate(name="Test Create", type="test", location="Test Room")

    response = client.post("/api/devices", json=new_device.model_dump(mode="json"))
    assert response.status_code == 200

    data = response.json()

    assert data["name"] == new_device.name
    assert data["type"] == new_device.type
    assert data["location"] == new_device.location
    assert data["status"] == DeviceStatus.CLOSED

    devices = client.get("/api/devices").json()

    ids = [d["id"] for d in devices]
    assert data["id"] in ids


def test_get_device_valid(client, uuids):
    response = client.get(f"/api/devices/{uuids["window"]}")
    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(uuids["window"])
    assert data["name"] == "Room Window"
    assert data["type"] == "Window"
    assert data["location"] == "Room 1"
    assert data["status"] in DeviceStatus
    assert "battery" in data
    assert "last_updated" in data
    assert "last_seen" in data


def test_get_device_invalid(client, uuids):
    response = client.get(f"/api/devices/{uuids["invalid"]}")
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Device not found"


def test_update_device_valid(client, uuids):

    update_data = DeviceUpdate(status=DeviceStatus.OFFLINE.value, last_updated=datetime.now())

    response = client.patch(f"/api/devices/{uuids["window"]}", json=update_data.model_dump(exclude_unset=True, mode="json"))
    assert response.status_code == 200

    data = response.json()

    assert data["status"] == DeviceStatus.OFFLINE
    assert data["id"] == str(uuids["window"])

    new_response = client.get(f"/api/devices/{uuids["window"]}").json()
    assert new_response["status"] == DeviceStatus.OFFLINE


def test_update_device_invalid(client, uuids):
    update_data = DeviceUpdate(status=DeviceStatus.OFFLINE.value, last_updated=datetime.now())

    response = client.patch(f"/api/devices/{uuids["invalid"]}", json=update_data.model_dump(exclude_unset=True, mode="json"))
    assert response.status_code == 404

    data = response.json()
    assert data["detail"] == "Device not found"


def test_delete_device_valid(client, uuids):
    response = client.delete(f"/api/devices/{uuids["window"]}")

    assert response.status_code == 200
    
    data = response.json()
    assert data == "Deleted device successfully"

    new_response = client.get(f"/api/devices/{uuids["window"]}")
    assert new_response.status_code == 404


def test_delete_device_invalid(client, uuids):
    response = client.delete(f"/api/devices/{uuids["invalid"]}")
    assert response.status_code == 404
    
    data = response.json()

    assert data["detail"] == "Error deleting device"


def test_trigger_valid_device(client, uuids):
    response = client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open")
    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert "device" in data
    assert "event" in data

    assert data["device"]["status"] == DeviceStatus.OPEN.value
    assert data["device"]["id"] == str(uuids["window"])

    assert data["event"]["type"] == EventType.STATUS_CHANGE.value
    assert data["event"]["device_id"] == str(uuids["window"])


def  test_trigger_invalid_device(client, uuids):
    response = client.get(f"/api/devices/{uuids["invalid"]}/trigger?new_status=open")
    assert response.status_code == 404

    data = response.json()
    
    assert data["detail"] == "Device not found"