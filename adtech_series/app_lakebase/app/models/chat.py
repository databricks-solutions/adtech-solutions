from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from .base import Base


class MessageType(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatSession(Base):
    __tablename__ = 'chat_sessions'

    id = Column(String, primary_key=True)  # UUID
    user_name = Column(String, nullable=False, index=True)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    messages = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_updated', 'user_name', 'updated_at'),
    )


class ChatHistory(Base):
    __tablename__ = 'chat_history'

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_name = Column(String, nullable=False, index=True)
    message_type = Column(Enum(MessageType), nullable=False)
    message_content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_order = Column(Integer, nullable=False)

    session = relationship("ChatSession", back_populates="messages")

    # One-to-one relationship to embedding
    embedding = relationship("MessageEmbedding", back_populates="message", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        Index('idx_chat_user_order', 'chat_id', 'user_name', 'message_order'),
    )


