from sqlmodel import Session, select
from typing import List, Any
from backend.app.models import Device, DeviceUpdate, Event

def get_devices(*, session: Session) -> List[Device]:
    return session.exec(select(Device)).all()

def get_device_by_id(*, session: Session, device_id: int) -> Device | None:
    return session.get(Device, device_id)

def update_device(*, session: Session, db_device: Device, new_device: DeviceUpdate) -> Any:
    device_data = new_device.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(device_data)
    session.add(db_device)
    session.commit()
    session.refresh(db_device)
    return db_device

def create_device(*, session: Session, device: Device) -> Device:
    session.add(device)
    session.commit()
    session.refresh(device)
    return device

def create_event(*, session: Session, event: Event) -> Event:
    session.add(event)
    session.commit()
    session.refresh(event)
    return event