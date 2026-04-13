from enum import Enum
from typing import Dict, List, Set, Union
from pydantic import BaseModel, Field, ConfigDict


from src.domain.parse_core.common.enums import GRAPHQLBuiltInTypesEnum
from src.domain.parse_core.schemas.common_schema import ProjectSchema


class GraphqlProjectDefinition(ProjectSchema):
    app_prefix: str = Field(default="/graphql")


class FieldSchema(BaseModel):
    type: Union[str, GRAPHQLBuiltInTypesEnum]
    is_enum: bool = False
    not_null: bool = False
    is_array: bool = False
    not_null_elements: bool = False
    directives: Dict[str, Dict[str, str]]

    model_config = ConfigDict(use_enum_values=True)


class GraphqlLocationsEnum(Enum):
    SCHEMA = "SCHEMA"
    SCALAR = "SCALAR"
    OBJECT = "OBJECT"
    FIELD_DEFINITION = "FIELD_DEFINITION"
    ARGUMENT_DEFINITION = "ARGUMENT_DEFINITION"
    INTERFACE = "INTERFACE"
    UNION = "UNION"
    ENUM = "ENUM"
    ENUM_VALUE = "ENUM_VALUE"
    INPUT_OBJECT = "INPUT_OBJECT"
    INPUT_FIELD_DEFINITION = "INPUT_FIELD_DEFINITION"
    QUERY = "QUERY"
    MUTATION = "MUTATION"
    SUBSCRIPTION = "SUBSCRIPTION"
    FIELD = "FIELD"
    FRAGMENT_DEFINITION_FRAGMENT_SPREAD = "FRAGMENT_DEFINITION & FRAGMENT_SPREAD"
    INLINE_FRAGMENT = "INLINE_FRAGMENT"
    VARIABLE_DEFINITION = "VARIABLE_DEFINITION"


class DirectiveSchema(BaseModel):
    arguments: Dict[str, FieldSchema]
    locations: List[GraphqlLocationsEnum]

    model_config = ConfigDict(use_enum_values=True)


class InterfaceSchema(BaseModel):
    fields: Dict[str, FieldSchema]
    directives: Dict[str, Dict[str, str]]


class TypeSchema(InterfaceSchema):
    interfaces: List = []


class QuerySchema(FieldSchema):
    arguments: Dict[str, FieldSchema]


class InputSchema(InterfaceSchema): ...


class EnumSchema(BaseModel):
    directives: Dict[str, Dict[str, str]]


class MutationSchema(FieldSchema):
    arguments: Dict[str, FieldSchema]


class GraphqlSchemaSchema(BaseModel):
    directives: Dict[str, DirectiveSchema]
    interfaces: Dict[str, InterfaceSchema]
    types: Dict[str, TypeSchema]
    queries: Dict[str, QuerySchema]
    inputs: Dict[str, InputSchema]
    enums: Dict[str, Dict[str, EnumSchema]]
    mutations: Dict[str, MutationSchema]


class GraphqlProjectSchema(BaseModel):
    project: GraphqlProjectDefinition
    graphql_schema: GraphqlSchemaSchema
