from fastapi import APIRouter, HTTPException

from backend.app import crud
from backend.app.api.deps import sessionDep
from backend.app.models import EventPublic
from backend.app.core.config import logger

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[EventPublic])
async def get_events(session: sessionDep, limit: int = 10):
    """
        Get recent events
    """
    logger.info(f"Event data requested with a limit of: {limit}")

    try:
        events = crud.get_events(session=session, limit=limit)

        logger.debug(f"Retrieved {len(events)} events from database")
        
        return events
    
    except Exception:
        logger.exception("Error retrieving events")
        raise HTTPException(status_code=500, detail="Internal server error")