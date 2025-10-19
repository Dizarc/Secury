from fastapi import APIRouter, HTTPException
from datetime import datetime

from backend.app import crud
from backend.app.api.deps import sessionDep
from backend.app.core.websocket import manager
from backend.app.core.config import logger
from backend.app.models import (
    DevicePublic, DeviceCreate, DeviceUpdate, DeviceStatus,
    EventCreate, EventType, EventPublic
)

import uuid


router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DevicePublic])
async def get_all_devices(session: sessionDep):
    """
        Get a list of all devices
    """
    logger.info("Request to list all devices is received")

    try:
        devices = crud.get_devices(session=session)
        logger.debug(f"Retrieved {len(devices)} devices from database")
        
        return devices
    
    except Exception:
        logger.exception("Error retrieving device list")
        raise HTTPException(status_code=500, detail="Internal server error")


#TODO: Create test for this
#==========================================
@router.post("", response_model=DevicePublic)
async def create_device(device_in: DeviceCreate, session: sessionDep):
    """
        Create new device
    """
    logger.info(f"Device creation request received: {device_in.model_dump(mode="json")}")

    try:
        device = crud.create_device(session=session, device=device_in)
        device_data = DevicePublic.model_validate(device).model_dump(mode="json")
        logger.info(f"New device creation posted with data: {device_data}")

        await manager.broadcast({
            "type": "device_added",
            "device": device_data
        })

        return device
    
    except Exception:
        logger.exception("Unexpected error during device creation")
        raise HTTPException(status_code=500, detail="Failed to create device")


#==========================================
@router.get("/{device_id}", response_model=DevicePublic)
async def get_device(device_id: uuid.UUID, session: sessionDep):
    """
        Get specific device by ID
    """
    logger.info(f"device retrieval requested with id: {device_id}")

    try:
        device = crud.get_device_by_id(session=session, device_id=device_id)

        if not device:
            logger.warning(f"Device: {device_id} not found")
            raise HTTPException(status_code=404, detail="Device not found")
        
        logger.debug(f"Device: {device_id} data retrieved successfully")
        
        return device
    
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error retrieving device with id: {device_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


#TODO: create test for this
#==========================================
@router.patch("/{device_id}", response_model=DevicePublic)
async def update_device(device_id: uuid.UUID, device_in: DeviceUpdate, session: sessionDep):
    """
        Update Device
    """
    logger.info(f"Device update requested with id: {device_id} and data {device_in.model_dump()}")

    try:
        device = crud.get_device_by_id(session=session, device_id=device_id)

        if not device:
            logger.warning(f"Device: {device_id} not found for update")
            raise HTTPException(status_code=404, detail="Device not found")
        
        updated_device = crud.update_device(session=session, db_device=device, device_in=device_in)

        logger.info(f"Device: {device_id} updated successfully")

        await manager.broadcast({
            "type": "device_updated",
            "device": DevicePublic.model_validate(updated_device).model_dump(mode="json")
        })

        return updated_device
    
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error updating device with id: {device_id}")
        raise HTTPException(status_code=500, detail="Internal server error")

#TODO: add tests for this
#==========================================
@router.delete("/{device_id}", response_model=str)
async def delete_device(device_id: uuid.UUID, session: sessionDep):
    """
        Delete User
    """
    logger.info(f"Device deletion requested with device id: {device_id}")

    try:
        success = crud.delete_device(session=session, device_id=device_id)

        if not success:
            logger.warning(f"Failed to delete device: {device_id}")
            raise HTTPException(status_code=404, detail="Error deleting device")
        
        logger.info(f"Device: {device_id} deleted successfully")

        await manager.broadcast({
            "type": "device_deleted",
            "device_id": device_id
        })

        return "Deleted device successfully"
    
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Error deleting device: {device_id}")
        raise HTTPException(status_code=500, detail="Internal server error")


#==========================================
@router.get("/{device_id}/trigger", response_model=dict)
async def trigger_device(
    device_id: uuid.UUID, 
    new_status: str, 
    session: sessionDep,
    battery: int | None = None
):
    """
        Device state change for open/closed with battery percentage
        Will be called by the IoT devices
    """
    logger.info(f"Device state change requested with device id: {device_id}, new status: {new_status} and battery: {battery}")

    device = crud.get_device_by_id(session=session, device_id=device_id)

    try:
        if not device:
            logger.warning(f"Device with id: {device_id} is not found")
            raise HTTPException(status_code=404, detail="Device not found")
        
        if new_status not in DeviceStatus:
            logger.warning(f"Device with id: {device_id} is not found")
            raise HTTPException(status_code=400, detail="Status is invalid")
        
        update_data = {
            "status": new_status,
            "last_updated": datetime.now(),
        }

        if battery is not None:
            if 0 <= battery <= 100:
                update_data["battery"] = battery
            else:
                logger.warning(f"Battery value {battery} is out of range (0-100)")
                raise HTTPException(status_code=400, detail="Battery must be 0-100")

        logger.debug(f"Updating device: {device_id} with: {update_data}")
        device_in_update = DeviceUpdate(**update_data) 
        
        device = crud.update_device(session=session, db_device=device, device_in=device_in_update)

        event_details = f"status changed to {new_status}"
        if battery is not None:
            event_details += f" (battery: {battery}%)"

        logger.debug(f"Creating event for device {device_id}: {event_details}")

        event = crud.create_event(
            session=session, 
            event=EventCreate(
                device_id = device_id,
                type=EventType.STATUS_CHANGE,
                details=event_details,
            ),
        )

        if battery is not None and battery < 10:
            logger.warning(f"Device {device_id} has low battery: {battery}%")
            crud.create_event(
                session=session, 
                event=EventCreate(
                    device_id = device_id,
                    type=EventType.BATTERY_LOW,
                    details=f"battery low: {battery}%",
                ),
            )

        logger.info(f"Successfully updated {device_id}")

        return {
            "success": True,
            "device": DevicePublic.model_validate(device).model_dump(mode="json"),
            "event": EventPublic.model_validate(event).model_dump(mode="json"),
        }
    
    except HTTPException as e:
        logger.error(f"HTTP error while triggering device: {device_id}: {e.detail}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while processing trigger for device: {device_id}")
        raise HTTPException(status_code=500, detail="Internal server error")