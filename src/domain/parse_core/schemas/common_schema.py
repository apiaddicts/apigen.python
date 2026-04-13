from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from src.domain.parse_core.common.enums import DataDriver


class ValidationsSchema(BaseModel):
    type: Optional[str] = None
    min: Optional[str] = None
    max: Optional[str] = None
    regex: Optional[str] = None
    value: Optional[str] = None
    integer: Optional[str] = None
    fraction: Optional[str] = None
    inclusive: Optional[str] = None


class ProjectSchema(BaseModel):
    name: str
    description: str
    version: str
    prefix: Optional[str] = ""
    data_driver: DataDriver = Field(alias="data-driver")

    model_config = ConfigDict(use_enum_values=True, populate_by_name=True)
