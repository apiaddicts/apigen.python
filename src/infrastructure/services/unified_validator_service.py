import os
from typing import Union, Dict, Any, Awaitable
from fastapi import UploadFile
from src.infrastructure.models.validator_models import ValidationFailure
from src.infrastructure.services.validators.graphql_validator_service import GraphQLValidatorService
from src.infrastructure.services.validators.openapi_parser_service import OpenAPIParserService
from src.infrastructure.services.validators.asyncapi_parser_service import AsyncAPIParserService
from src.infrastructure.services.generators.graphql_generator_service import GraphQLGeneratorService
from src.infrastructure.services.generators.openapi_generator_service import OpenAPIGeneratorService
from src.infrastructure.services.generators.asyncapi_generator_service import AsyncAPIGeneratorService
from src.infrastructure.services.zip_service import ZipService

class UnifiedValidatorService:
    @staticmethod
    async def _validate_with_parser(file: UploadFile, parser_class) -> Dict[str, Any]:
        content = await file.read()
        content_str = content.decode("utf-8")
        format_type = 'json' if file.filename and file.filename.endswith('.json') else 'yaml'
        parser = parser_class()
        return parser.validate(content=content_str, format_type=format_type)

    @staticmethod
    async def _process_validation(
        validation_awaitable: Awaitable[Dict[str, Any]],
        generator_service,
        spec_type: str,
        existing_project_dir: str = None,
    ) -> Union[str, ValidationFailure, Dict[str, Any]]:
        try:
            result = await validation_awaitable

            if result["valid"]:
                generated_result = generator_service.generate(
                    result["content"],
                    existing_project_dir=existing_project_dir,
                )

                if isinstance(generated_result, dict):
                    return generated_result

                return ZipService.compress_directory(generated_result)
            else:
                return ValidationFailure(
                    is_valid=False,
                    message=f"{spec_type} validation failed",
                    errors=result["errors"]
                )
        except Exception as e:
            return ValidationFailure(
                is_valid=False,
                message=f"{spec_type} validation error: {str(e)}"
            )

    @staticmethod
    async def validate_file(
        file: UploadFile,
        file_type: str,
        existing_project_dir: str = None,
    ) -> Union[str, ValidationFailure]:
        if file_type == "graphql":
            return await UnifiedValidatorService._process_validation(
                GraphQLValidatorService.validate(file),
                GraphQLGeneratorService,
                "GraphQL",
                existing_project_dir=existing_project_dir,
            )
        
        elif file_type == "openapi":
            return await UnifiedValidatorService._process_validation(
                UnifiedValidatorService._validate_with_parser(file, OpenAPIParserService),
                OpenAPIGeneratorService,
                "OpenAPI",
                existing_project_dir=existing_project_dir,
            )
        
        elif file_type == "asyncapi":
            return await UnifiedValidatorService._process_validation(
                UnifiedValidatorService._validate_with_parser(file, AsyncAPIParserService),
                AsyncAPIGeneratorService,
                "AsyncAPI",
                existing_project_dir=existing_project_dir,
            )
        
        else:
            return ValidationFailure(is_valid=False, message="Unsupported file type")
