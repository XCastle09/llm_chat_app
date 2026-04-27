from pydantic import BaseModel, Field
from typing import Optional

class UserRegister(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=3)

class UserLogin(BaseModel):
    login: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str

class MessageCreate(BaseModel):
    message: str

class ChatCreate(BaseModel):
    title: str