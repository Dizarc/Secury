from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

from backend.app.api.deps import sessionDep, fake_hash
from backend.app import crud


router = APIRouter(prefix="/login", tags=["login"])

@router.post("/access-token")
def login_access_token(session: sessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = crud.get_user(session=session, email=form_data.username)
    
    hashed_password = fake_hash(form_data.password)
    if (not user) or (not hashed_password == user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {"access_token": user.email, "token_type": "bearer"}