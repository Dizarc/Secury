from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import timedelta

from backend.app import crud
from backend.app.models import Token
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.api.deps import sessionDep


router = APIRouter(prefix="/login", tags=["login"])


@router.post("/access-token")
def login_access_token(session: sessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    access_token = create_access_token(data=user.email, expires_delta= access_token_expires)

    return Token(access_token=access_token)