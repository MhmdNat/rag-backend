from pydantic import BaseModel, Field
from typing import Optional


class FeedbackRequest(BaseModel):
    run_id: str                          # the run_id returned from /api/query
    score: int = Field(..., ge=0, le=1)  # 1 = thumbs up, 0 = thumbs down
    comment: Optional[str] = None        # optional free-text feedback


class FeedbackResponse(BaseModel):
    feedback_id: str
    run_id: str
    score: int
    message: str