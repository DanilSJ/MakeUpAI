from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import HTTPException, Depends
from fastapi.security import (
    OAuth2PasswordBearer,
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt.exceptions import InvalidTokenError, InvalidKeyError
from pydantic import BaseModel
from starlette import status
from core.config import auth_settings

security = HTTPBearer()


class Token(BaseModel):
    access_token: str
    token_type: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login/")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        auth_settings.PRIVATE_KEY.read_text(),
        algorithm=auth_settings.ALGORITHM,
    )

    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        try:
            payload = jwt.decode(
                token,
                auth_settings.PUBLIC_KEY.read_text(),
                algorithms=[auth_settings.ALGORITHM],
            )

            user_id = payload.get("sub")

            if user_id is None:
                raise credentials_exception

            return {"id": int(user_id)}
        except InvalidKeyError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
    except InvalidTokenError:
        raise credentials_exception


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Извлекает Bearer токен из заголовка Authorization"""
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=403, detail="Invalid authentication scheme")
    return credentials.credentials