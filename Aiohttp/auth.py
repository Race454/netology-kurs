import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field
from aiohttp import web

from config import config
from models import User
from database import db


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class TokenData(BaseModel):
    user_id: str
    username: str


class AuthMiddleware:
    @staticmethod
    async def get_current_user(request: web.Request) -> Optional[TokenData]:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        
        try:
            payload = jwt.decode(
                token, 
                config.JWT_SECRET, 
                algorithms=[config.JWT_ALGORITHM]
            )
            return TokenData(
                user_id=payload["user_id"],
                username=payload["username"]
            )
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def create_access_token(user_data: TokenData) -> str:
        expires_delta = timedelta(minutes=config.JWT_EXPIRATION_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "user_id": user_data.user_id,
            "username": user_data.username,
            "exp": expire
        }
        
        return jwt.encode(
            payload, 
            config.JWT_SECRET, 
            algorithm=config.JWT_ALGORITHM
        )
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )


async def register_user(username: str, password: str) -> Optional[User]:
    async with db.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == username)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            return None
        
        user = User(
            username=username,
            password_hash=AuthMiddleware.hash_password(password)
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    async with db.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user or not AuthMiddleware.verify_password(password, user.password_hash):
            return None
        
        return user