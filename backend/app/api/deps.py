import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from backend.app import crud
from backend.app.models import User, TokenPayload
from backend.app.core.database import engine
from backend.app.core.config import settings
from backend.app.core.security import ALGORITHM


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login/access-token")

def get_session():
    with Session(engine) as session:
        yield session

sessionDep = Annotated[Session, Depends(get_session)]

tokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(session: sessionDep, token: tokenDep):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])

        token_data = TokenPayload(**payload)

    except (InvalidTokenError, ValidationError):
        raise credentials_exception
    
    user = crud.get_user_by_email(session=session, email=token_data.sub)
    if not user:
        raise credentials_exception

    return user

CurrentUser = Annotated[User, Depends(get_current_user)]
