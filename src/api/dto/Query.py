from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    query: str
    user_id: int = Field(default=1)
    chat_id: Optional[int] = Field(default=None)


class QueryResponse(BaseModel):
    run_id: str          
    query: str
    rewritten_query: str
    answer: str