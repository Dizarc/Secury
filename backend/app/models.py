from sqlmodel import SQLModel, Field
from datetime import datetime

# Add create classes

class Device(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    type: str
    location: str
    status: str = "closed"
    battery: int = 100
    last_updated: datetime = Field(default_factory=datetime.now)

class DeviceUpdate(SQLModel):
    status: str | None = None
    last_updated: datetime | None = None

class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id")
    type: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.now)