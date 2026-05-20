from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..redis_client import redis_client
from ..config import settings
from ..models import User
from ..schemas import TokenResponse
import httpx

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        payload = {"sub": str(user_id), "exp": expire, "type": "access"}
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def create_refresh_token(user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(days=30)
        payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        redis_client.setex(f"refresh:{user_id}", timedelta(days=30), token)
        return token

    @staticmethod
    def verify_refresh_token(user_id: int, token: str) -> bool:
        stored = redis_client.get(f"refresh:{user_id}")
        return stored is not None and stored == token

    @staticmethod
    def delete_refresh_token(user_id: int):
        redis_client.delete(f"refresh:{user_id}")

    @staticmethod
    async def register_user(user_data, db: AsyncSession):
        # Проверки
        login = user_data.login.strip()
        password = user_data.password
        if not login or not password:
            raise HTTPException(400, "Login and password cannot be empty")
        if len(login) < 3:
            raise HTTPException(400, "Login must be at least 3 characters")
        if len(password) < 3:
            raise HTTPException(400, "Password must be at least 3 characters")

        # Проверка уникальности
        result = await db.execute(select(User).where(User.login == login))
        if result.scalar_one_or_none():
            raise HTTPException(400, "Login already exists")

        hashed = AuthService.hash_password(password)
        user = User(login=login, hashed_password=hashed)
        db.add(user)
        await db.commit()
        return {"msg": "ok"}

    @staticmethod
    async def login_user(user_data, db: AsyncSession):
        result = await db.execute(select(User).where(User.login == user_data.login))
        user = result.scalar_one_or_none()
        if not user or not AuthService.verify_password(user_data.password, user.hashed_password):
            raise HTTPException(401, "Invalid login or password")
        access = AuthService.create_access_token(user.id)
        refresh = AuthService.create_refresh_token(user.id)
        return TokenResponse(access_token=access, refresh_token=refresh)

    @staticmethod
    async def refresh_access_token(refresh_token_dict: dict, db: AsyncSession):
        token = refresh_token_dict.get('refresh_token')
        if not token:
            raise HTTPException(400, "refresh_token required")
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            if payload.get("type") != "refresh":
                raise HTTPException(401)
            user_id = int(payload.get("sub"))
        except:
            raise HTTPException(401, "Invalid refresh token")
        if not AuthService.verify_refresh_token(user_id, token):
            raise HTTPException(401, "Refresh token expired or invalid")
        new_access = AuthService.create_access_token(user_id)
        return {"access_token": new_access}

    @staticmethod
    async def github_callback(code: str, db: AsyncSession):
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
                headers={"Accept": "application/json"},
            )
            token_data = resp.json()
            if "error" in token_data:
                raise HTTPException(400, "GitHub OAuth failed")
            github_token = token_data["access_token"]
            user_resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {github_token}"}
            )
            gh_user = user_resp.json()
            github_id = str(gh_user["id"])
            login = gh_user["login"]

        result = await db.execute(select(User).where(User.github_id == github_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(login=login, github_id=github_id)
            db.add(user)
            await db.commit()
        access_token = AuthService.create_access_token(user.id)
        refresh_token = AuthService.create_refresh_token(user.id)
        return RedirectResponse(f"/?access_token={access_token}&refresh_token={refresh_token}")