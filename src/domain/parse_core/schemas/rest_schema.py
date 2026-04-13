from typing import Dict
from pydantic import BaseModel, Field, ConfigDict

from src.domain.parse_core.schemas.router_schema import RouterSchema
from src.domain.parse_core.schemas.entity_schema import EntitySchema
from src.domain.parse_core.schemas.common_schema import ProjectSchema
from src.domain.parse_core.common.enums import DataDriver


class OpenApiProjectSchema(ProjectSchema):
    data_driver: DataDriver = Field(alias="data-driver")
    prefix: str = Field(default="")
    model_config = ConfigDict(populate_by_name=True)


class RESTProjectSchema(BaseModel):
    project: OpenApiProjectSchema
    entities: Dict[str, EntitySchema]
    routers: Dict[str, RouterSchema]
