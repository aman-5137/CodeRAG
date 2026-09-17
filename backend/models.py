from pydantic import BaseModel, Field

class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, ge=1, le=10)

class ImpactRequest(BaseModel):
    target: str
