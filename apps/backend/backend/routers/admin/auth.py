from http import HTTPStatus
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from chatlib.utils.env_helper import get_env_variable
from chatlib.utils.time import get_timestamp
import jwt
from backend.env_variables import ADMIN_HASHED_PASSWORD, ADMIN_ID, AUTH_SECRET
from backend.routers.admin.common import check_admin_credential
from backend.routers.errors import ErrorType


router = APIRouter()

class LoginCredential(BaseModel):
    password: str

class AuthenticationResult(BaseModel):
    jwt: str

@router.post("/login", response_model=AuthenticationResult)
async def login_with_code(credential: LoginCredential):
    import bcrypt
    if bcrypt.checkpw(credential.password.encode(), get_env_variable(ADMIN_HASHED_PASSWORD).encode()):
        issued_at = get_timestamp()/1000
        to_encode = {
            "sub": get_env_variable(ADMIN_ID),
            "iat": issued_at,
            "exp": issued_at + (365 * 24 * 3600)
        }
        access_token = jwt.encode(to_encode, get_env_variable(AUTH_SECRET), algorithm='HS256')
        return AuthenticationResult(jwt=access_token)
    else:
        raise HTTPException(status_code=400, detail=ErrorType.NoSuchUser)

@router.get("/token", dependencies=[Depends(check_admin_credential)], status_code=200)
async def verify_token():
    return