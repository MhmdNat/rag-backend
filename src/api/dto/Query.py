from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)
    index: str = Field(default="RAGDocs")


class QueryResponse(BaseModel):
    run_id: str          
    query: str
    rewritten_query: str
    answer: str