from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from .database import get_db
from .config import settings
from .models import User

oauth2_scheme = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
        if payload.get("type") != "access":
            raise HTTPException(401, "Invalid token type")
    except JWTError:
        raise HTTPException(401, "Invalid token")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(401, "User not found")
    return user