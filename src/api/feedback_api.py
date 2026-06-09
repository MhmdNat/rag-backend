import os
from contextlib import asynccontextmanager

import dotenv
from fastapi import FastAPI, HTTPException
from langsmith import Client

from src.api.dto.Query import QueryRequest, QueryResponse
from src.api.dto.Feedback import FeedbackRequest, FeedbackResponse
from src.query.retriever import close_retriever_client
from src.embeddings.model import create_embedding_model
from src.query.reranker import get_model
from src.query.web_pipeline import run_web_rag_pipeline
from langsmith import traceable

import asyncio
from fastapi.responses import StreamingResponse

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
    yield
    close_retriever_client()

app = FastAPI(
    title="RAG Feedback API",
    description="Run RAG queries and collect human feedback via LangSmith",
    version="1.0.0",
    lifespan=lifespan,
)



@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query", response_model=QueryResponse)
@traceable(name="query_endpoint")
async def query_endpoint(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="No query was provided")
    
    try:
        # We call the generator, which will handle both the tokens and the trailing metadata
        generator = run_web_rag_pipeline(
            query_text=request.query,
            index_name=request.index,
            top_k=request.top_k
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
