import hashlib
import secrets
from jose import jwt
from datetime import datetime, timedelta, timezone
from ..redis_client import redis_client
from ..config import settings

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        # Простое хэширование с солью (для учебного проекта)
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((salt + password).encode())
        return f"{salt}:{hash_obj.hexdigest()}"

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            salt, hash_value = hashed.split(":")
            hash_obj = hashlib.sha256((salt + plain).encode())
            return hash_obj.hexdigest() == hash_value
        except:
            return False

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