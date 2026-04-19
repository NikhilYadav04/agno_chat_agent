from pydantic import BaseModel, Field
from typing import List, Optional


class Output(BaseModel):
    id: str = Field(description="Unique identifier for the response message")
    message: str = Field(
        description="Brief summary if isTable=true, full answer if isTable=false"
    )
    isTable: bool = Field(
        default=False, description="True when response contains tabular data"
    )
    tableColumns: Optional[List[str]] = Field(
        default=None, description="Column headers — required when isTable=true"
    )
    tableRows: Optional[List[List[str]]] = Field(
        default=None,
        description="2D array of string values — required when isTable=true",
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0"
    )
