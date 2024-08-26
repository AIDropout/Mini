from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, Field


class SavedMemoryMetadataSchema(BaseModel):
    text: str = Field(..., description="Text of the memory segment")
    date: Optional[str] = Field(
        None,
        description="Specific date associated with the memory, in YYYY-MM-DD format or null if none found",
    )
    relevance: Literal["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM", "LIFETIME"] = Field(
        ..., description="Relevance category of the memory segment"
    )
    owner: Literal["USER", "ASSISTANT"] = Field(
        ..., description="Owner of the memory segment"
    )


class RetrievedMemoryMetadataSchema(BaseModel):
    relevance: List[
        Union[Literal["SHORT_TERM", "MEDIUM_TERM", "LONG_TERM", "LIFETIME"], None]
    ] = Field(
        ...,
        description="List of relevance categories of the memory segments, or null if none found",
    )
    date: List[Optional[str]] = Field(
        default_factory=list,
        description="List of specific dates associated with the memory, in YYYY-MM-DD format or null if none found",
    )
    query: Optional[str] = Field(
        None,
        description="Natural language query string to recall relevant information, or null if no query is needed",
    )


class MemoryMetadataSchema(BaseModel):
    segments: List[SavedMemoryMetadataSchema] = Field(
        ..., description="List of memory segments"
    )


class MemoryRecordSchema(BaseModel):
    agent_id: str
    created_at: datetime  # relevant
    hash: str
    id: str
    memory: str  # relevant
    metadata: dict  # relevant
    score: float
    updated_at: Optional[datetime]  # relevant
    user_id: str
