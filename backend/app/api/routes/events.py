from fastapi import APIRouter

from backend.app import crud
from backend.app.core.database import sessionDep
from backend.app.models import EventPublic

router = APIRouter(prefix="/events", tags=["events"])

@router.get("", response_model=list[EventPublic])
async def get_events(session: sessionDep, limit: int = 10):
    """
        Get recent events
    """
    events = crud.get_events(session=session, limit=limit)
    
    return events