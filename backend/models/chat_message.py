# Chat message model for agent conversation history
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base


class ConversationRole(enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # "patient_coach" or "doctor_assistant"
    role = Column(Enum(ConversationRole), nullable=False)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", Text, nullable=True)  # JSON: exercise_type, patient_id, used_llm, safety_escalation
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User")

    __table_args__ = (
        Index("ix_chat_messages_user_agent_created", "user_id", "agent_type", "created_at"),
    )
