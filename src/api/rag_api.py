import os
from contextlib import asynccontextmanager

import dotenv
from fastapi import FastAPI, HTTPException
from langsmith import Client

from src.db.db import init_db
from src.api.dto.Query import QueryRequest, QueryResponse, RegenerateRequest
from src.api.dto.Feedback import FeedbackRequest, FeedbackResponse
from src.query.retriever import close_retriever_client
from src.embeddings.model import create_embedding_model
from src.query.reranker import get_model
from src.query.web_pipeline import run_web_rag_pipeline
from langsmith import traceable

import asyncio
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

import src.api.service.message as message_service
from typing import Optional


dotenv.load_dotenv()

langsmith_client = Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        raise RuntimeError("LANGCHAIN_API_KEY is not set in environment.")
    await asyncio.to_thread(create_embedding_model)
    await asyncio.to_thread(get_model)
    print("LangSmith connection OK.")
    await asyncio.to_thread(init_db)
    print("Database initialized.")
    yield
    close_retriever_client()


app = FastAPI(
    title="RAG Feedback API",
    description="Run RAG queries and collect human feedback via LangSmith",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
@traceable(name="query_endpoint")
async def query_endpoint(request: QueryRequest):
    print("new request received")
    if not request.query:
        raise HTTPException(status_code=400, detail="No query was provided")

    user_id = 1  # hardcoded until auth is implemented

    try:
        chat_id, message_id = await asyncio.to_thread(
            message_service.save_message,
            content=request.query,
            user_id=user_id,
            chat_id=request.chat_id,
            role="user",
        )
        print(f"Saved user message with id {message_id} in chat {chat_id}")
    except Exception as e:
        print(f"Error saving user message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving user message: {str(e)}")

    try:
        generator = run_web_rag_pipeline(
            query_text=request.query,
            user_id=user_id,
            chat_id=chat_id,
            query_id=message_id,
            parent_message_id=None,  # first response — no parent
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/api/regenerate")
@traceable(name="regenerate_endpoint")
async def regenerate_endpoint(request: RegenerateRequest):
    """
    Re-run the RAG pipeline for an existing query and stream a new response version.
    The new assistant message is saved with parent_message_id = root_assistant_message_id
    so all versions are linked.
    """
    user_id = 1  # hardcoded until auth is implemented

    try:
        generator = run_web_rag_pipeline(
            query_text=request.original_query,
            user_id=user_id,
            chat_id=request.chat_id,
            query_id=request.query_message_id,
            parent_message_id=request.root_assistant_message_id,
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration pipeline error: {str(e)}")


@app.post("/api/feedback", response_model=FeedbackResponse)
@traceable(name="submit_feedback")
def submit_feedback(request: FeedbackRequest):
    try:
        query_message_id = request.query_message_id
        answer_message_id = request.answer_message_id
        rating = request.rating
        if rating not in (0, 1):
            raise HTTPException(status_code=400, detail=f"Invalid rating value: {rating}. Must be 0 or 1.")
        if rating == 0 and not request.reason:
            raise HTTPException(status_code=400, detail="Reason is required when rating is 0.")
        reason = request.reason
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid feedback request: {str(e)}")

    feedback_response = message_service.save_feedback(
        chat_id=request.chat_id,
        query_message_id=query_message_id,
        answer_message_id=answer_message_id,
        rating=rating,
        reason=reason,
    )
    return feedback_response


@app.get("/api/chats")
def get_chats(user_id: int = 1):
    return message_service.get_chats_for_user(user_id)


@app.get("/api/chats/{chat_id}/messages")
def get_messages(chat_id: int, user_id: int = 1):
    # Returns versioned message list — see message_service.get_messages_for_chat docstring
    return message_service.get_messages_for_chat(chat_id, user_id)


@app.delete("/api/chats/{chat_id}/user/{user_id}")
def delete_chat(chat_id: Optional[int], user_id: int):
    print(f"Request to delete chat {chat_id} for user {user_id}")
    success = message_service.delete_chat(chat_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Chat not found or does not belong to user")
    return {"message": "Chat deleted"}
