from sqlmodel import Session, select
from typing import List, Any
from datetime import datetime, timedelta

from backend.app.models import (
    Device, DeviceUpdate, DevicePublic, DeviceCreate, DeviceStatus, 
    Event, EventCreate, EventType
)

def get_devices(*, session: Session) -> List[Device]:
    return session.exec(select(Device)).all()

def get_device_by_id(*, session: Session, device_id: int) -> Device | None:
    return session.get(Device, device_id)

def update_device(*, session: Session, db_device: Device, new_device: DeviceUpdate) -> Any:
    """
        Updates device (Only stuff inside DeviceUpdate)
    """
    device_data = new_device.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(device_data)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

def check_offline_devices(*, session: Session, timeout_minutes: int = 10) -> List[Device]:
    """
        Mark devices offline if not seen recently.
        Returns a list of devices marked offline
    """
    cutoff = datetime.now() - timedelta(minutes=timeout_minutes)
    offline_devices = session.exec(
        select(Device).where(
            Device.last_seen < cutoff,
            Device.status != DeviceStatus.OFFLINE
        )
    ).all()

    for device in offline_devices:
        device.status = DeviceStatus.OFFLINE
        session.add(device)

        create_event(
            session=session,
            event=EventCreate(
                device_id=device.id,
                type = EventType.DEVICE_OFFLINE,
                details=f"{device.name} has gone offline"
            ),
        )
    
    if offline_devices:
        session.commit()

    return offline_devices

def create_device(*, session: Session, device: DeviceCreate) -> Device:
    db_obj = Device.model_validate(device)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj

def get_events(*, session: Session, limit) -> List[Event]:
    return session.exec(select(Event).order_by(Event.timestamp).limit(limit=limit)).all()

def create_event(*, session: Session, event: EventCreate) -> Event:
    db_obj = Event.model_validate(event)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj
