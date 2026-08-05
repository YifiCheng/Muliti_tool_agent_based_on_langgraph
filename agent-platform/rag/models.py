from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    source: str
    content: str
    section: str = ""
    chunk_index: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    chunk: DocumentChunk
    score: float
    retriever: str