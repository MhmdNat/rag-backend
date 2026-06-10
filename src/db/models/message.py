from sqlalchemy import ForeignKey, String, text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.db import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False) # user or assistant
    content: Mapped[str] = mapped_column(String(5000), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")