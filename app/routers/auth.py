from fastapi import APIRouter, Depends, Body
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..schemas import UserRegister, UserLogin
from ..services.auth_service import AuthService
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    return await AuthService.register_user(user_data, db)

@router.post("/login")
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await AuthService.login_user(user_data, db)

@router.post("/refresh")
async def refresh(refresh_token: dict = Body(...), db: AsyncSession = Depends(get_db)):
    return await AuthService.refresh_access_token(refresh_token, db)

@router.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?client_id={settings.GITHUB_CLIENT_ID}&redirect_uri={settings.GITHUB_REDIRECT_URI}&scope=user:email"
    )

@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    return await AuthService.github_callback(code, db)