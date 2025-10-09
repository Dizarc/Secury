from sqlmodel import Session, select

from backend.app.models import Device, Event

def get_devices(*, session: Session) -> Device | None:
    return session.exec(select(Device)).all()

def get_device_by_id(*, session: Session, device_id: int) -> Device | None:
    return session.get(Device, device_id)

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