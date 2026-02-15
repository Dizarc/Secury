import uuid 

from sqlmodel import Session, select
from typing import List, Any
from datetime import datetime, timedelta

from backend.app.core.security import get_password_hash, verify_password
from backend.app.models import (
    Device, DeviceUpdate, DeviceCreate, DeviceStatus, 
    Event, EventCreate, EventType,
    User, UserCreate, UserUpdate
)


def get_devices(*, session: Session) -> List[Device]:
    return session.exec(select(Device)).all()


def get_device_by_id(*, session: Session, device_id: uuid.UUID) -> Device | None:
    return session.get(Device, device_id)


def update_device(*, session: Session, db_device: Device, device_in: DeviceUpdate) -> Device:
    device_data = device_in.model_dump(exclude_unset=True)
    db_device.sqlmodel_update(device_data)

    db_device.last_seen = datetime.now()

    session.add(db_device)
    session.commit()
    session.refresh(db_device)

    return db_device


def delete_device(*, session: Session, device_id: uuid.UUID) -> bool:
    device = session.get(Device, device_id)

    if device is None:
        return False
    
    session.delete(device)
    session.commit()
    
    return True


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
    device_data = device.model_dump(exclude_unset=True)

    if "status" not in device_data or device_data["status"] is None:
        device_data["status"] = DeviceStatus.CLOSED

    db_obj = Device(**device_data)
    
    db_obj.last_seen = datetime.now()
    
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    return db_obj


#==========================================
def get_events(*, session: Session, limit) -> List[Event]:
    return session.exec(select(Event).order_by(Event.timestamp).limit(limit=limit)).all()


def create_event(*, session: Session, event: EventCreate) -> Event:
    db_obj = Event.model_validate(event)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)

    return db_obj


#==========================================
def create_user(*, session: Session, user: UserCreate) -> User:
    db_obj = User.model_validate(
        user, 
        update={"hashed_password": get_password_hash(user.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)

    extra_data = {}

    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    
    db_user.sqlmodel_update(user_data, update=extra_data)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    return session.exec(select(User).filter(User.email == email)).first()


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user