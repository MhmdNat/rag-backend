
from src.db.db import SessionLocal
from src.db.models.message import Message
from src.db.models.chat import Chat
from src.db.models.user import User
from typing import Optional
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_chat(db, user_id: int, chat_title: str) -> Chat:
    chatModel = Chat(user_id=user_id, chat_title=chat_title)
    db.add(chatModel)
    db.commit()
    db.refresh(chatModel)
    return chatModel


def delete_chat(db, user_id: int, chat_id: int) -> bool:
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        return False
    db.delete(chat)
    db.commit()
    return True


def save_message(content: str, user_id: int, chat_id: Optional[int], role: str):
    db = SessionLocal()  # open a real session directly
    try:
        chat = None
        if chat_id is not None:
            chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
        if not chat:
            title = content[:20].strip()
            if len(content) > 20:
                title += "…"
            chat = Chat(user_id=user_id, chat_title=title)
            db.add(chat)
            db.commit()
            db.refresh(chat)

        message = Message(chat_id=chat.id, role=role, content=content)
        db.add(message)
        db.commit()
        db.refresh(message)
        return chat.id, message.id
    except Exception as e:
        print(f"Error in save_message: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def get_chats_for_user(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Chat).filter(Chat.user_id == user_id).all()
    finally:
        db.close()


def get_messages_for_chat(chat_id: Optional[int], user_id: int):
    db = SessionLocal()
    try:
        return db.query(Message).filter(Message.chat_id == chat_id, Chat.user_id == user_id).all()
    finally:
        db.close()


def delete_chat(chat_id: Optional[int], user_id: int):
    db = SessionLocal()
    print(f"Attempting to delete chat {chat_id} for user {user_id}")
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
        if not chat:
            return False
        db.delete(chat)
        db.commit()
        return True
    finally:
        db.close()