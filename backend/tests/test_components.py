"""
Test multiple components working together
"""
from fastapi import status
from backend.app.models import EventType, DeviceStatus


def test_trigger_creates_event(auth_client, uuids):

    events_before = auth_client.get("/api/events?limit=100").json()
    initial_count = len(events_before)

    response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open")
    assert response.status_code == status.HTTP_200_OK

    events_after = auth_client.get("/api/events?limit=100").json()
    new_count = len(events_after)

    assert new_count > initial_count

    latest_event = events_after[0]
    assert latest_event["device_id"] == str(uuids["window"])
    assert latest_event["type"] == EventType.STATUS_CHANGE.value


def test_trigger_updates_device_state(auth_client, uuids):
    
    device_before = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    initial_status = device_before["status"]

    if initial_status == DeviceStatus.CLOSED.value:
        new_status = DeviceStatus.OPEN.value
    else:
        new_status = DeviceStatus.CLOSED.value

    response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status={new_status}")
    assert response.status_code == status.HTTP_200_OK

    device_after = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    assert device_after["status"] == new_status
    assert device_after["status"] != initial_status


def test_low_battery_creates_two_events(auth_client, uuids):

    response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open&battery=6")
    assert response.status_code == status.HTTP_200_OK

    events = auth_client.get("/api/events?limit=10").json()

    event_types = [event["type"] for event in events]

    assert EventType.STATUS_CHANGE in event_types
    assert EventType.BATTERY_LOW in event_types

def test_multiple_device_triggers(auth_client, uuids):

    for name, device_id in list(uuids.items())[:3]:
        print(device_id)
        response = auth_client.get(f"/api/devices/{device_id}/trigger?new_status=open")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["device"]["id"] == str(device_id)
        assert data["device"]["status"] == DeviceStatus.OPEN.value

    all_devices = auth_client.get("/api/devices").json()
    uuid_values = [str(v) for v in uuids.values()]
    for device in all_devices:
        if device["id"] in uuid_values:
            assert device["status"] == DeviceStatus.OPEN.value

def test_device_state_persists_across_multiple_requests(auth_client, uuids):

    auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open")

    for _ in range(3):
        device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
        assert device["status"] == DeviceStatus.OPEN.value

    auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=closed")

    for _ in range(3):
        device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
        assert device["status"] == DeviceStatus.CLOSED.value

def test_battery_update_persists(auth_client, uuids):

    battery_levels = [100, 75, 50, 25]

    for battery in battery_levels:
        response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open&battery={battery}")
        assert response.status_code == status.HTTP_200_OK

        device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
        assert device["battery"] == battery

def test_websocket_receives_device_updates(auth_client):

    with auth_client.websocket_connect("/ws") as websocket:
        initial = websocket.receive_json()
        assert initial["type"] == "initial_state"

        websocket.send_text("test")
        ack = websocket.receive_json()
        assert ack["type"] == "ack"

def test_api_error_handling(auth_client, uuids):

    invalid_requests = [
        (f"api/devices/{uuids["invalid"]}", status.HTTP_404_NOT_FOUND),
        (f"api/devices/{uuids["invalid"]}/trigger?new_status=open", status.HTTP_404_NOT_FOUND),
        (f"api/devices/{uuids["window"]}/trigger?new_status=invalid", status.HTTP_404_NOT_FOUND),
        (f"api/devices/{uuids["window"]}/trigger?new_status=open&battery=150", status.HTTP_400_BAD_REQUEST),
    ]

    for endpoint, expected_status in invalid_requests:
        response = auth_client.get(endpoint)
        assert response.status_code == expected_status
        assert "detail" in response.json()

def test_battery_zero_valid_percentage(auth_client, uuids):

    response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open&battery=0")
    assert response.status_code == status.HTTP_200_OK
    
    device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    assert device["battery"] == 0

def test_battery_hundred_valid_percentage(auth_client, uuids):

    response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status=open&battery=100")
    assert response.status_code == status.HTTP_200_OK
    
    device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    assert device["battery"] == 100

def test_full_device_lifecycle(auth_client, uuids):
    """
        test: check status -> trigger -> verify event -> check new status
    """
    initial_device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    initial_status = initial_device["status"]
    initial_battery = initial_device["battery"]

    if initial_status == DeviceStatus.CLOSED.value:
        new_status = DeviceStatus.OPEN.value
    else:
        new_status = DeviceStatus.CLOSED.value

    new_battery = 80

    trigger_response = auth_client.get(f"/api/devices/{uuids["window"]}/trigger?new_status={new_status}&battery={new_battery}")
    assert trigger_response.status_code == status.HTTP_200_OK
    trigger_data = trigger_response.json()

    assert trigger_data["success"] is True
    assert trigger_data["device"]["status"] == new_status
    assert trigger_data["device"]["battery"] == new_battery
    assert trigger_data["event"]["type"] == EventType.STATUS_CHANGE.value

    updated_device = auth_client.get(f"/api/devices/{uuids["window"]}").json()
    
    assert updated_device["status"] == new_status
    assert updated_device["battery"] == new_battery

    events = auth_client.get("/api/events?limit=5").json()
    latest_event = events[0]
    
    assert latest_event["device_id"] == str(uuids["window"])
    assert latest_event["type"] == EventType.STATUS_CHANGE.value
    assert new_status in latest_event["details"]