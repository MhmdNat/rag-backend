
from db.db import SessionLocal
from db.models.message import Message
from db.models.chat import Chat
from db.models.user import User
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


def save_message(db, content: str, user_id: int, chat_id: int, role: str) -> str:
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    if not chat:
        #create chat if it doesn't exist
        chat = create_chat(db, user_id=user_id, chat_title="New Chat") # change this to something more meaningful later

    messageModel = Message(chat_id=chat.id, role=role, content=content, role=role)
    db.add(messageModel)
    db.commit()
    db.refresh(messageModel)
    return messageModel