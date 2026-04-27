from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    login = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    github_id = Column(String(50), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String(10))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chat = relationship("Chat", back_populates="messages")