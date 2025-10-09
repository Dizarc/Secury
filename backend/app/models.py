from sqlmodel import SQLModel, Field
from datetime import datetime

class Device(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    type: str
    location: str
    status: str = "closed"
    battery: int = 100
    last_updated: datetime = Field(default_factory=datetime.now)

class Event(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    device_id: int = Field(foreign_key="device.id")
    event_type: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.now)