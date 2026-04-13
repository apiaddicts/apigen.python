from pydantic import BaseModel, Field
from typing import List, Optional


class AsyncapiContract(BaseModel):
    spec: dict = Field(..., description="The asyncapi spec of the project")
