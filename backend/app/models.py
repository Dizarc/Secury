from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum
from pydantic import EmailStr

import uuid

class DeviceStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    OFFLINE = "offline"

class EventType(str, Enum):
    STATUS_CHANGE = "status_change"
    DEVICE_OFFLINE = "device_offline"
    BATTERY_LOW = "battery_low"

class DeviceBase(SQLModel):
    name: str = Field(index=True)
    type: str
    location: str
    battery: int = Field(default=100)

class Device(DeviceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    status: DeviceStatus = Field(default=DeviceStatus.CLOSED)
    last_updated: datetime = Field(default_factory= lambda: datetime.now())
    last_seen: datetime = Field(default_factory= lambda: datetime.now())

class DevicePublic(DeviceBase):
    id: uuid.UUID
    status: DeviceStatus
    last_updated: datetime
    last_seen: datetime

class DeviceCreate(DeviceBase):
    status: DeviceStatus | None = None

# TODO: Add the last updated here with a datetime?
class DeviceUpdate(SQLModel):
    name: str | None = None
    type: str | None = None
    location: str | None = None
    status: DeviceStatus | None = None
    battery: int | None = None
    last_updated: datetime | None = None
    
#==========================================
class EventBase(SQLModel):
    device_id: uuid.UUID = Field(foreign_key="device.id")
    type: EventType
    details: str

class Event(EventBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class EventPublic(EventBase):
    id: uuid.UUID
    timestamp: datetime

class EventCreate(EventBase):
    pass

#==========================================
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)

class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str 

class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)

class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)

class UserPublic(UserBase):
    id: uuid.UUID