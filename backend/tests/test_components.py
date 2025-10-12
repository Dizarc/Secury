"""
Test multiple components working together
"""
from app.models import EventType, DeviceStatus

def test_trigger_creates_event(client):

    events_before = client.get("/api/events?limit=100").json()
    initial_count = len(events_before)

    response = client.get("/api/devices/1/trigger?new_status=open")
    assert response.status_code == 200

    events_after = client.get("/api/events?limit=100").json()
    new_count = len(events_after)

    assert new_count > initial_count

    latest_event = events_after[0]
    assert latest_event["device_id"] == 1
    assert latest_event["type"] == EventType.STATUS_CHANGE.value

def test_trigger_updates_device_state(client):
    
    device_before = client.get("/api/devices/1").json()
    initial_status = device_before["status"]

    if initial_status == DeviceStatus.CLOSED.value:
        new_status = DeviceStatus.OPEN.value
    else:
        new_status = DeviceStatus.CLOSED.value

    response = client.get(f"/api/devices/1/trigger?new_status={new_status}")
    assert response.status_code == 200

    device_after = client.get("/api/devices/1").json()
    assert device_after["status"] == new_status
    assert device_after["status"] != initial_status

def test_low_battery_creates_two_events(client):
    response = client.get("/api/devices/1/trigger?new_status=open&battery=6")
    assert response.status_code == 200

    events = client.get("/api/events?limit=10").json()

    event_types = [event["type"] for event in events]

    assert EventType.STATUS_CHANGE in event_types
    assert EventType.BATTERY_LOW in event_types

def test_multiple_device_triggers(client):
    devices = [1, 2, 3]

    for device_id in devices:
        response = client.get(f"/api/devices/{device_id}/trigger?new_status=open")
        assert response.status_code == 200

        data = response.json()

        assert data["device"]["id"] == device_id
        assert data["device"]["status"] == DeviceStatus.OPEN.value

    all_devices = client.get("/api/devices").json()
    for device in all_devices:
        if device["id"] in devices:
            assert device["status"] == DeviceStatus.OPEN.value

def test_device_state_persists_across_multiple_requests(client):
    client.get(f"/api/devices/1/trigger?new_status=open")

    for _ in range(3):
        device = client.get("/api/devices/1").json()
        assert device["status"] == DeviceStatus.OPEN.value

    client.get("/api/devices/1/trigger?new_status=closed")

    for _ in range(3):
        device = client.get("/api/devices/1").json()
        assert device["status"] == DeviceStatus.CLOSED.value

def test_battery_update_persists(client):
    battery_levels = [100, 75, 50, 25]

    for battery in battery_levels:
        response = client.get(f"/api/devices/1/trigger?new_status=open&battery={battery}")
        assert response.status_code == 200

        device = client.get("/api/devices/1").json()
        assert device["battery"] == battery

def test_websocket_receives_device_updates(client):
    with client.websocket_connect("/ws") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "initial_state"

        websocket.send_text("test")
        ack = websocket.receive_json()
        assert ack["type"] == "ack"

def test_api_error_handling(client):
    invalid_requests = [
        ("api/devices/999", 404),
        ("api/devices/999/trigger?new_status=open", 404),
        ("api/devices/1/trigger?new_status=invalid", 400),
        ("api/devices/1/trigger?new_status=open&battery=150", 400),
    ]

    for endpoint, expected_status in invalid_requests:
        response = client.get(endpoint)
        assert response.status_code == expected_status
        assert "detail" in response.json()

def test_battery_zero_valid_percentage(client):
    response = client.get("/api/devices/1/trigger?new_status=open&battery=0")
    assert response.status_code == 200
    
    device = client.get("/api/devices/1").json()
    assert device["battery"] == 0

def test_battery_hundred_valid_percentage(client):
    response = client.get("/api/devices/1/trigger?new_status=open&battery=100")
    assert response.status_code == 200
    
    device = client.get("/api/devices/1").json()
    assert device["battery"] == 100

def test_full_device_lifecycle(client):
    """
        test: check status -> trigger -> verify event -> check new status
    """
    initial_device = client.get("/api/devices/1").json()
    initial_status = initial_device["status"]
    initial_battery = initial_device["battery"]

    if initial_status == DeviceStatus.CLOSED.value:
        new_status = DeviceStatus.OPEN.value
    else:
        new_status = DeviceStatus.CLOSED.value

    new_battery = 80

    trigger_response = client.get(f"/api/devices/1/trigger?new_status={new_status}&battery={new_battery}")
    assert trigger_response.status_code == 200
    trigger_data = trigger_response.json()

    assert trigger_data["success"] is True
    assert trigger_data["device"]["status"] == new_status
    assert trigger_data["device"]["battery"] == new_battery
    assert trigger_data["event"]["type"] == EventType.STATUS_CHANGE.value

    updated_device = client.get("/api/devices/1").json()
    
    assert updated_device["status"] == new_status
    assert updated_device["battery"] == new_battery

    events = client.get("/api/events?limit=5").json()
    latest_event = events[0]
    
    assert latest_event["device_id"] == 1
    assert latest_event["type"] == EventType.STATUS_CHANGE.value
    assert new_status in latest_event["details"]