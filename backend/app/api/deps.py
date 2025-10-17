from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from typing import Annotated

from backend.app.core.database import engine
from backend.app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

def get_session():
    with Session(engine) as session:
        yield session

sessionDep = Annotated[Session, Depends(get_session)]

tokenDep = Annotated[str, Depends(oauth2_scheme)]

# TODO: create Security stuff(follow: https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/)
# def get_current_user(session: sessionDep, token: tokenDep) -> User:

# CurrentUser = Annotated[User, Depends(get_current_user)]