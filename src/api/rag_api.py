import os
from contextlib import asynccontextmanager

import dotenv
from fastapi import FastAPI, HTTPException
from langsmith import Client

from src.db.db import init_db
from src.api.dto.Query import QueryRequest, QueryResponse
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
from src.api.service.message import get_db

dotenv.load_dotenv()

langsmith_client = Client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        raise RuntimeError("LANGCHAIN_API_KEY is not set in environment.")
    # Warm the heavy shared models once per API process so requests reuse them.

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
    "http://localhost:5173", # Default Vite port
    "http://localhost:3000", # Default CRA port
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
    print("new request recieved")
    if not request.query:
        raise HTTPException(status_code=400, detail="No query was provided")
    
    #user_id = request.user_id  # this should later be extracted from jwt not passed by frontend
    #if not user_id:
    #    raise HTTPException(status_code=400, detail="No user_id provided in request")
    
    #save user message
    try:
        chat_id, message_id = await asyncio.to_thread(
            message_service.save_message, 
            content=request.query, 
            user_id=1, 
            chat_id=request.chat_id, 
            role="user")
        print(f"Saved user message with id {message_id} in chat {chat_id}")
    except Exception as e:
        print(f"Error saving user message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error saving user message: {str(e)}")
    
    try:
        # We call the generator, which will handle both the tokens and the trailing metadata
        generator = run_web_rag_pipeline(
            query_text=request.query,
            user_id=1,
            chat_id=chat_id
        )
        
        return StreamingResponse(
            generator, 
            media_type="text/event-stream" # Tells the browser to listen for structured events
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.post("/api/feedback", response_model=FeedbackResponse)
@traceable(name="submit_feedback")
def submit_feedback(request: FeedbackRequest):
    try:
        feedback = langsmith_client.create_feedback(
            run_id=request.run_id,
            key="human_feedback",          # label shown in LangSmith dashboard
            score=request.score,           # 0 or 1
            comment=request.comment,       # optional text
            feedback_source_type="api",    # marks this as coming from your app
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangSmith error: {str(e)}")

    label = "thumbs_up" if request.score == 1 else "thumbs_down"

    return FeedbackResponse(
        feedback_id=str(feedback.id),
        run_id=request.run_id,
        score=request.score,
        message=f"Feedback recorded: {label}",
    )
