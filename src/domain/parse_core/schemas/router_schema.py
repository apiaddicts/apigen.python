from enum import Enum
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

from src.domain.parse_core.common.enums import AttributeTypeEnum, EndpointMethodEnum
from src.domain.parse_core.schemas.common_schema import ValidationsSchema


class ResponseAttrubuteSchema(BaseModel):
    name: str
    type: Union[str, AttributeTypeEnum]
    entity_field_name: str
    ref_model: Optional[str] = None
    validations: Optional[ValidationsSchema]

    model_config = ConfigDict(use_enum_values=True)


class ResponseSchema(BaseModel):
    is_collection: bool
    attributes: list[ResponseAttrubuteSchema]
    mime_type: str = "application/json"


class RequestAttributesSchema(BaseModel):
    name: str
    entity_field_name: str
    type: Union[str, AttributeTypeEnum]

    model_config = ConfigDict(use_enum_values=True)


class RequestSchema(BaseModel):
    is_collection: bool = False
    attributes: list[RequestAttributesSchema]
    mime_type: str = Field(alias="mime-type", default="application/json")


class ParameterTypeEnum(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"


class ParameterLocationEnum(Enum):
    PATH = "path"
    QUERY = "query"
    HEADERS = "headers"
    COOKIE = "cookie"


class ParameterSchema(BaseModel):
    is_collection: bool
    name: str
    type: ParameterTypeEnum
    required: bool
    location: ParameterLocationEnum = Field(alias="in")
    default: Any = None
    validations: ValidationsSchema

    model_config = ConfigDict(use_enum_values=True)


class EndpointSchema(BaseModel):
    method: EndpointMethodEnum
    mapping: (
        str  # id of the resource if is (get, put, delete) for a specific one "/{id}"
    )
    name: str
    parameters: Optional[list[ParameterSchema]] = None
    response: Optional[ResponseSchema]
    responses: Dict[int, Dict[str, Any]] = Field(default_factory=dict, description="Full response definitions including errors")
    request: Optional[RequestSchema]
    response_schema_name: Optional[str] = None
    response_wrapper_field: Optional[str] = None

    model_config = ConfigDict(use_enum_values=True)


class RouterSchema(BaseModel):
    entity: str
    mapping: str
    endpoints: list[EndpointSchema]
    sub_routers: Optional[Dict[str, "RouterSchema"]] = None

    def get_subrouter(self, path):
        return self.sub_routers[path]

    model_config = ConfigDict(validate_assignment=True)
