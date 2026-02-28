from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class QueryBase(BaseModel):
    query_text: str

class QueryCreate(QueryBase):
    response_text: str
    user_id: int

class QueryResponse(QueryBase):
    id: int
    response_text: str
    created_at: datetime

    class Config:
        from_attributes = True