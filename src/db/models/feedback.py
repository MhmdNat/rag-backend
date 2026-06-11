from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.db import Base

class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id"), nullable=False)

    query_message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)
    answer_message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"), nullable=False)

    rating: Mapped[int] = mapped_column() # 1 or 0 for thumbs up or down
    reason: Mapped[str | None] = mapped_column(String(1000)) # required if rating is 0