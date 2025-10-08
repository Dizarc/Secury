from typing import Annotated
from sqlmodel import Session, create_engine, SQLModel

from backend.app.core.config import settings
#from app.models import Device?

connect_args = {"check_same_thread": False}
engine = create_engine(str(settings.DATABASE_URL), connect_args=connect_args)

def init_db(session: Session) -> None:
    SQLModel.metadata.create_all(engine)