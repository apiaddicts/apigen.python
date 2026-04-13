from typing import Dict, Optional

from pydantic import BaseModel, Field
from src.domain.parse_core.common.enums import DataDriver
from src.domain.parse_core.schemas.entity_schema import EntitySchema
from src.domain.parse_core.schemas.common_schema import ProjectSchema


class AsyncProjectSchema(ProjectSchema):
    data_driver: Optional[DataDriver] = Field(alias="data-driver", default=None)


class AsyncApiProjectSchema(BaseModel):
    project: AsyncProjectSchema
    default_content_type: str = Field(default="application/json")
    servers: Dict[str, Dict]
    channels: Dict[str, Dict]
    operations: Dict[str, Dict]
    entities: Dict[str, EntitySchema]
    components: Dict
