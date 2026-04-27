from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from ..database import get_db
from ..models import User
from ..schemas import UserRegister, UserLogin, TokenResponse
from ..services.auth_service import AuthService
from ..config import settings
import httpx


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Дополнительная проверка на пустые значения
    if not user_data.login or not user_data.login.strip():
        raise HTTPException(400, "Login cannot be empty")
    if not user_data.password or not user_data.password.strip():
        raise HTTPException(400, "Password cannot be empty")
    
    # Проверка длины
    if len(user_data.login) < 3:
        raise HTTPException(400, "Login must be at least 3 characters")
    if len(user_data.password) < 3:
        raise HTTPException(400, "Password must be at least 3 characters")
    
    result = await db.execute(select(User).where(User.login == user_data.login))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Login already exists")
    hashed = AuthService.hash_password(user_data.password)
    user = User(login=user_data.login, hashed_password=hashed)
    db.add(user)
    await db.commit()
    return {"msg": "ok"}

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.login == user_data.login))
    user = result.scalar_one_or_none()
    if not user or not AuthService.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(401, "Invalid login or password")
    access = AuthService.create_access_token(user.id)
    refresh = AuthService.create_refresh_token(user.id)
    return TokenResponse(access_token=access, refresh_token=refresh)

@router.post("/refresh")
async def refresh(refresh_token: str = Body(...), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(401)
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(401, "Invalid refresh token")
    if not AuthService.verify_refresh_token(user_id, refresh_token):
        raise HTTPException(401, "Refresh token expired or invalid")
    new_access = AuthService.create_access_token(user_id)
    return {"access_token": new_access}

@router.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_REDIRECT_URI}&scope=user:email"
    )

@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
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