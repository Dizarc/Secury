from datetime import datetime, timedelta

from backend.app import crud
from backend.app.models import Device, DeviceCreate, DeviceUpdate, DeviceStatus, EventCreate, EventType

def test_get_devices(session):
    devices = crud.get_devices(session=session)
    
    assert len(devices) == 3
    assert all(hasattr(d, "name") for d in devices)

def test_get_devices_by_id_valid(session):
    device = crud.get_device_by_id(session=session, device_id=1)

    assert device is not None
    assert device.id == 1
    assert device.name == "Room Window"

def test_get_device_by_id_invalid(session):
    device = crud.get_device_by_id(session=session, device_id=999)
    
    assert device is None

def test_create_device(session):
    new_device = DeviceCreate(
        name = "Test Device",
        type = "Test Type",
        location = "Test Room",
        battery = 100
    )

    created = crud.create_device(session=session, device=new_device)
    
    assert created.id is not None
    assert created.name == "Test Device"
    assert created.type == "Test Type"
    assert created.battery == 100

def test_update_device_status(session):
    device = crud.get_device_by_id(session=session, device_id=1)
    
    original_status = device.status

    if original_status == DeviceStatus.CLOSED:
        new_status = DeviceStatus.OPEN
    else:
        new_status = DeviceStatus.CLOSED

    update_data = DeviceUpdate(status=new_status)

    updated_device = crud.update_device(session=session, db_device=device, new_device=update_data)
    
    assert  updated_device.status == new_status

def test_update_device_battery(session):
    device = crud.get_device_by_id(session=session, device_id=1)

    update_data = DeviceUpdate(battery=40)

    updated_device = crud.update_device(session=session, db_device=device, new_device=update_data)

    assert updated_device.battery == 40

def test_update_device_status_and_battery(session):
    device = crud.get_device_by_id(session=session, device_id=2)
    
    original_status = device.status

    if original_status == DeviceStatus.CLOSED:
        new_status = DeviceStatus.OPEN
    else:
        new_status = DeviceStatus.CLOSED

    update_data = DeviceUpdate(status=new_status, battery=50)

    updated_device = crud.update_device(session=session, db_device=device, new_device=update_data)
    
    assert  updated_device.status == new_status
    assert updated_device.battery == 50

def test_check_offline_devices(session):
    device = crud.get_device_by_id(session=session,device_id=1)
    
    device.last_seen = datetime.now() - timedelta(minutes=30)
    device.status = DeviceStatus.CLOSED

    session.add(device)
    session.commit()

    offline_devices = crud.check_offline_devices(session=session, timeout_minutes=20)

    assert len(offline_devices) > 0
    assert any(d.id == 1 for d in offline_devices)

    device = crud.get_device_by_id(session=session, device_id=1)
    assert device.status == DeviceStatus.OFFLINE

def test_check_offline_devices_no_change(session):
    """
        Test that recently seen devices are not marked as offline
    """
    devices = crud.get_devices(session=session)
    
    for device in devices:
        device.last_seen = datetime.now()

        device.status = DeviceStatus.CLOSED
        session.add(device)
    
    session.commit()

    offline_devices = crud.check_offline_devices(session=session, timeout_minutes=20)

    assert len(offline_devices) == 0

#==========================================
def test_create_event(session):
    event_data = EventCreate(
        device_id = 1,
        type = EventType.STATUS_CHANGE,
        details = "Test Event"
    )

    event = crud.create_event(session=session, event=event_data)

    assert event.id is not None
    assert event.device_id == 1
    assert event.type == EventType.STATUS_CHANGE
    assert event.details == "Test Event"
    assert event.timestamp is not None

def test_get_events_with_limit(session):
    for i in range(15):
        crud.create_event(
            session = session,
            event = EventCreate(
                device_id = 1,
                type = EventType.STATUS_CHANGE,
                details=f"Event {i}"
            )
        )
    
    events = crud.get_events(session=session, limit=5)

    assert len(events) == 5
