import base64
from typing import Dict, Any
from fastapi import UploadFile
from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    build_schema,
    validate_schema,
    GraphQLSyntaxError,
    parse,
    GraphQLInterfaceType,
)

class GraphQLValidatorService:
    """
    Validates GraphQL schemas using graphql-core.
    Supports GraphQL Oct 2021 specification (aligned with graphql-js v16/v17).
    Backward compatible with older standard schemas.
    """
    @staticmethod
    async def validate(file: UploadFile) -> Dict[str, Any]:
        try:
            content = await file.read()
            content_str = content.decode("utf-8")
            
            # First validate the schema structure
            schema = build_schema(content_str)
            errors = validate_schema(schema)
            
            if errors:
                error_messages = [str(e) for e in errors]
                return {
                    "valid": False,
                    "errors": error_messages
                }
            
            parse(content_str)  # Ensure it parses successfully as requested
            
            return {
                "valid": True,
                "content": content_str,
                "errors": []
            }
        except GraphQLSyntaxError as e:
            return {
                "valid": False,
                "errors": [f"Invalid GraphQL schema: {str(e)}"]
            }
        except TypeError as e:
            raw_msg = str(e)
            errors = [part.strip() for part in raw_msg.split("\n\n") if part.strip()]
            return {
                "valid": False,
                "errors": errors
            }
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Unexpected error: {str(e)}"]
            }

    @staticmethod
    def build_schema_from_string(definition_str: str) -> Dict[str, Any]:
        return build_schema(definition_str)

    @staticmethod
    def is_interface(definition) -> Dict[str, Any]:
        return isinstance(definition, GraphQLInterfaceType)

    @staticmethod
    def is_enum(definition) -> Dict[str, Any]:
        return isinstance(definition, GraphQLEnumType)

    @staticmethod
    def is_type(definition) -> Dict[str, Any]:
        return isinstance(definition, GraphQLObjectType)

    @staticmethod
    def is_input(definition) -> Dict[str, Any]:
        return isinstance(definition, GraphQLInputObjectType)

    @staticmethod
    def is_not_null(type_definition) -> Dict[str, Any]:
        return isinstance(type_definition, GraphQLNonNull)

    @staticmethod
    def is_list(type_definition) -> Dict[str, Any]:
        return isinstance(type_definition, GraphQLList)
