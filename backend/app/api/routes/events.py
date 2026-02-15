from fastapi import APIRouter, HTTPException, status

from backend.app import crud
from backend.app.api.deps import sessionDep, CurrentUser
from backend.app.models import EventPublic
from backend.app.core.config import logger

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[EventPublic])
async def get_events(session: sessionDep, current_user: CurrentUser, limit: int = 10):
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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")