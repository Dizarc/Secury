from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.app import crud
from backend.app.api.deps import sessionDep
from backend.app.core.websocket import manager
from backend.app.models import (
    DevicePublic, DeviceCreate, DeviceUpdate, DeviceStatus,
    EventCreate, EventType, EventPublic
)

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("", response_model=list[DevicePublic])
async def get_all_devices(session: sessionDep):
    """
        Get a list of all devices
    """
    devices = crud.get_devices(session=session)

    return devices

#TODO: Create test for this
#==========================================
@router.post("", response_model=DevicePublic)
async def create_device(device_in: DeviceCreate, session: sessionDep):
    """
        Create new device
    """
    device = crud.create_device(session=session, device=device_in)

    await manager.broadcast({
        "type": "device_added",
        "device": DevicePublic.model_validate(device).model_dump(mode="json")
    })

    return device

#==========================================
@router.get("/{device_id}", response_model=DevicePublic)
async def get_device(device_id: int, session: sessionDep):
    """
        Get specific device by ID
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

#TODO: create test for this
#==========================================
@router.patch("/{device_id}", response_model=DevicePublic)
async def update_device(device_id: int, device_in: DeviceUpdate, session: sessionDep):
    """
        Update Device
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    updated_device = crud.update_device(session=session, db_device=device, device_in=device_in)

    await manager.broadcast({
        "type": "device_updated",
        "device": DevicePublic.model_validate(updated_device).model_dump(mode="json")
    })

    return updated_device

#TODO: add tests for this
#==========================================
@router.delete("/{device_id}", response_model=str)
async def delete_device(device_id: int, session: sessionDep):
    """
        Delete User
    """
    success = crud.delete_device(session=session, device_id=device_id)

    if not success:
        raise HTTPException(status_code=404, detail="Error deleting device")
    
    await manager.broadcast({
        "type": "device_deleted",
        "device_id": device_id
    })

    return "Deleted device successfully"

#==========================================
@router.get("/{device_id}/trigger", response_model=dict)
async def trigger_device(
    device_id: int, 
    new_status: str, 
    session: sessionDep,
    battery: int | None = None
):
    """
        Device state change for open/closed with battery percentage
        Will be called by the IoT devices
    """
    device = crud.get_device_by_id(session=session, device_id=device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    if new_status not in DeviceStatus:
        raise HTTPException(status_code=400, detail="Status is invalid")
    
    update_data = {
        "status": new_status,
        "last_updated": datetime.now(),
    }

    if battery is not None:
        if 0 <= battery <= 100:
            update_data["battery"] = battery
        else:
            raise HTTPException(status_code=400, detail="Battery must be 0-100")

    device_in_update = DeviceUpdate(**update_data)
    
    device = crud.update_device(session=session, db_device=device, device_in=device_in_update)

    event_details = f"status changed to {new_status}"
    if battery is not None:
        event_details += f" (battery: {battery}%)"

    event = crud.create_event(
        session=session, 
        event=EventCreate(
            device_id = device_id,
            type=EventType.STATUS_CHANGE,
            details=event_details,
        ),
    )

    if battery is not None and battery < 10:
        crud.create_event(
            session=session, 
            event=EventCreate(
                device_id = device_id,
                type=EventType.BATTERY_LOW,
                details=f"battery low: {battery}%",
            ),
        )

    return {
        "success": True,
        "device": DevicePublic.model_validate(device).model_dump(mode="json"),
        "event": EventPublic.model_validate(event).model_dump(mode="json"),
    }
