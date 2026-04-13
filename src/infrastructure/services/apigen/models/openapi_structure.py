from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class EndpointSchema(BaseModel):
    method: str
    path: str
    request: Optional[str] = None
    response: Optional[str] = None
    params: Optional[Dict[str, str]] = None

class RouterSchema(BaseModel):
    basePath: str
    binding: str
    mapping: Optional[Dict[str, str]] = None
    endpoints: Dict[str, EndpointSchema]

class OpenAPIInterfaceContract(BaseModel):
    routers: Dict[str, RouterSchema] = Field(..., description="The openapi routers of the project")


class SchemaDefinition(BaseModel):
    extends: Optional[str] = None
    fields: Dict[str, str]

    @field_validator("fields")
    def validate_fields_not_empty(cls, v):
        if not v:
            raise ValueError("fields no puede estar vacío")
        return v

class OpenAPIDomainContract(BaseModel):
    schemas: Dict[str, SchemaDefinition] = Field(..., description="The schemas of the project")
