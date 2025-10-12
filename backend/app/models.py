from sqlmodel import SQLModel, Field
from datetime import datetime
from enum import Enum

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
    id: int | None = Field(default=None, primary_key=True)
    status: DeviceStatus = Field(default=DeviceStatus.CLOSED.value)
    last_updated: datetime = Field(default_factory= lambda: datetime.now())
    last_seen: datetime = Field(default_factory= lambda: datetime.now())

class DevicePublic(DeviceBase):
    id: int
    status: DeviceStatus
    last_updated: datetime
    last_seen: datetime

class DeviceCreate(DeviceBase):
    status: DeviceStatus | None = None

# TODO: Add the last updated here with a datetime?
class DeviceUpdate(SQLModel):
    status: DeviceStatus | None = None
    battery: int | None = None
    last_updated: datetime | None = None
    last_seen: datetime | None = None

#==========================================
class EventBase(SQLModel):
    device_id: int = Field(foreign_key="device.id")
    type: EventType
    details: str

class Event(EventBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now())

class EventPublic(EventBase):
    id: int
    timestamp: datetime

class EventCreate(EventBase):
    pass
