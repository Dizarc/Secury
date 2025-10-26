from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from typing import Annotated

from backend.app import crud
from backend.app.core.database import engine
from backend.app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login/access-token")

def get_session():
    with Session(engine) as session:
        yield session

sessionDep = Annotated[Session, Depends(get_session)]

tokenDep = Annotated[str, Depends(oauth2_scheme)]


def fake_hash(password: str):
    return "fake" + password


async def get_current_user(session: sessionDep, token: tokenDep):
    user = crud.get_user(session=session, email="john@example.com")

    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
