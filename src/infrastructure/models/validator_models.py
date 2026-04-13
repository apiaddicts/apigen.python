from typing import Optional, Union, Literal
from enum import Enum
from pydantic import BaseModel

class FileType(str, Enum):
    OPENAPI = "openapi"
    GRAPHQL = "graphql"
    ASYNCAPI = "asyncapi"

class ValidationSuccess(BaseModel):
    is_valid: Literal[True]
    content: str

class ValidationFailure(BaseModel):
    is_valid: Literal[False]
    message: str
    errors: Optional[list[str]] = None

ValidationResponse = Union[ValidationSuccess, ValidationFailure]
