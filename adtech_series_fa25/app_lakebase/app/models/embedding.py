from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from pgvector.sqlalchemy import Vector

from .base import Base


class MessageEmbedding(Base):
    __tablename__ = 'message_embeddings'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('chat_history.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    chat_id = Column(String, nullable=False, index=True)
    user_name = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False)
    embedding = Column(Vector(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationship back to the source message
    message = relationship("ChatHistory", back_populates="embedding", passive_deletes=True)

    __table_args__ = (
        Index('ix_message_embeddings_user_chat', 'user_name', 'chat_id'),
    )


