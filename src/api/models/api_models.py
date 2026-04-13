from typing import Optional
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    message: str
    details: Optional[str] = None
    errors: Optional[list[str]] = None
