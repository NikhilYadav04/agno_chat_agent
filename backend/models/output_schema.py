from pydantic import BaseModel, Field
from typing import List, Optional

class Output(BaseModel):
    id: str = Field(description="Unique identifier for the response message")
    message: str = Field(description="The main text response from the medical assistant")
    isTable: bool = Field(default=False, description="Set this to true if the response requires tabular data representation")
    tableRows: Optional[List[List[str]]] = Field(default=None, description="A 2D array of string values representing the rows of the table")
    tableColumns: Optional[List[str]] = Field(default=None, description="An array of column headers for the table data")
    confidence: float = Field(description="A confidence score between 0.0 and 1.0 indicating how certain the assistant is")
