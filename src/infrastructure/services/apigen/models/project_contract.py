from pydantic import BaseModel, Field, AliasChoices
from typing import Literal, Optional

class PythonProperties(BaseModel):
    artifact_id: str = Field(..., alias="artifact-id")

class ApigenProject(BaseModel):
    name: str
    description: str
    version: str
    python_properties: Optional[PythonProperties] = None
    data_driver: Literal["mysql", "oracle", "postgresql", "s3", "mssql"] = Field(..., validation_alias=AliasChoices("data-driver", "data_driver"))
