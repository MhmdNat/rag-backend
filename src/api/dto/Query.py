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


class RegenerateRequest(BaseModel):
    """
    Frontend sends the original assistant message id (the root of the version chain),
    the chat id, and the original query text so we can re-run the pipeline.
    """
    chat_id: int
    user_id: int = Field(default=1)
    original_query: str
    query_message_id: int          # the user message DB id
    root_assistant_message_id: int # id of the FIRST assistant message (parent_message_id for the new one)
