from src.api.dto.Feedback import FeedbackResponse
from src.db.db import SessionLocal
from src.db.models.message import Message
from src.db.models.chat import Chat
from src.db.models.user import User
from typing import Optional
from src.db.models.feedback import Feedback


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


def save_message(
    content: str,
    user_id: int,
    chat_id: Optional[int],
    role: str,
    parent_message_id: Optional[int] = None,
):
    db = SessionLocal()
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

        message = Message(
            chat_id=chat.id,
            role=role,
            content=content,
            parent_message_id=parent_message_id,
        )
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
    """
    Return messages for a chat, with assistant messages grouped into version chains.

    Each item in the returned list has the shape:
      { id, chat_id, role, content, created_at, context,
        versions: [{id, content, context}],   # only on assistant messages
        active_version_index: int,
        feedback: {rating, reason} | None }

    For user messages, `versions` is omitted.
    For assistant messages, `versions` holds ALL versions (oldest first) and
    `active_version_index` points at the last one (newest).
    The top-level `id` / `content` always mirror the active version.
    """
    db = SessionLocal()
    try:
        # Verify the chat belongs to the user
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
        if not chat:
            return []

        all_messages = (
            db.query(Message)
            .filter(Message.chat_id == chat_id)
            .order_by(Message.id.asc())
            .all()
        )

        # Bulk fetch all feedback for messages in this chat in a single query
        all_message_ids = [m.id for m in all_messages]
        feedback_map = {}
        if all_message_ids:
            feedbacks = db.query(Feedback).filter(Feedback.answer_message_id.in_(all_message_ids)).all()
            for f in feedbacks:
                feedback_map[f.answer_message_id] = {"rating": f.rating, "reason": f.reason}

        # Separate user messages and assistant messages
        result = []
        # Map from original_assistant_id -> list of version Message objects (in order)
        version_groups: dict[int, list[Message]] = {}

        for m in all_messages:
            if m.role == "user":
                result.append({
                    "id": m.id,
                    "chat_id": m.chat_id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })
            elif m.role == "assistant":
                if m.parent_message_id is None:
                    version_groups[m.id] = [m]
                else:
                    root_id = m.parent_message_id
                    if root_id not in version_groups:
                        version_groups[root_id] = []
                    version_groups[root_id].append(m)

        seen_roots = set()
        final_result = []
        for m in all_messages:
            if m.role == "user":
                final_result.append({
                    "id": m.id,
                    "chat_id": m.chat_id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })
            elif m.role == "assistant" and m.parent_message_id is None:
                if m.id in seen_roots:
                    continue
                seen_roots.add(m.id)
                versions = version_groups.get(m.id, [m])
                active_idx = len(versions) - 1
                active = versions[active_idx]

                # Check if any version of this message has feedback
                existing_feedback = None
                for v in versions:
                    if v.id in feedback_map:
                        existing_feedback = feedback_map[v.id]
                        break

                final_result.append({
                    "id": active.id,
                    "chat_id": active.chat_id,
                    "role": "assistant",
                    "content": active.content,
                    "created_at": active.created_at.isoformat() if active.created_at else None,
                    "versions": [
                        {"id": v.id, "content": v.content}
                        for v in versions
                    ],
                    "active_version_index": active_idx,
                    "feedback": existing_feedback,
                    "query_message_id": final_result[-1]["id"] if final_result and final_result[-1]["role"] == "user" else None,
                })

        return final_result
    finally:
        db.close()

def get_query_message_id_for_assistant(assistant_message_id: int) -> Optional[int]:
    """
    Given an assistant message id (any version), find the user message that
    immediately precedes the root assistant message in the same chat.
    Returns the user message id, or None if not found.
    """
    db = SessionLocal()
    try:
        msg = db.query(Message).filter(Message.id == assistant_message_id).first()
        if not msg:
            return None

        # Resolve to root
        root_id = msg.id if msg.parent_message_id is None else msg.parent_message_id
        root = db.query(Message).filter(Message.id == root_id).first()
        if not root:
            return None

        # Find the latest user message before the root in the same chat
        user_msg = (
            db.query(Message)
            .filter(
                Message.chat_id == root.chat_id,
                Message.role == "user",
                Message.id < root.id,
            )
            .order_by(Message.id.desc())
            .first()
        )
        return user_msg.id if user_msg else None
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


def save_feedback(chat_id: int, query_message_id: int, answer_message_id: int, rating: int, reason: Optional[str]):
    db = SessionLocal()
    try:
        feedback = Feedback(
            chat_id=chat_id,
            query_message_id=query_message_id,
            answer_message_id=answer_message_id,
            rating=rating,
            reason=reason
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return FeedbackResponse(feedback_id=feedback.id, message="Feedback saved successfully")
    finally:
        db.close()
