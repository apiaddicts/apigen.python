import json
import yaml
from typing import Union, Dict, Any
from src.infrastructure.services.apigen.generators.openapi_generator import OpenAPIGenerator
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
from src.infrastructure.services.apigen.validators.detailed_config_validator import DetailedConfigValidator
from src.infrastructure.services.apigen.x_apigen_schema_reference import get_validation_error_response

class OpenAPIGeneratorService:
    @staticmethod
    def generate(content: str, existing_project_dir: str = None) -> Union[str, Dict[str, Any]]:
        content_str = content
        try:
            try:
                spec_dict = json.loads(content_str)
            except json.JSONDecodeError:
                spec_dict = yaml.safe_load(content_str)
            
            validation_result = DetailedConfigValidator.validate(spec_dict)
            if not validation_result["all_valid"]:
                return get_validation_error_response(validation_result)

        except Exception:
            pass

        parser = OpenAPIParser()
        parser.load_definition(spec_str=content_str)
        project_schema = parser.parse()

        generator_service = OpenAPIGenerator()
        return generator_service.generate(
            project_schema,
            existing_project_dir=existing_project_dir,
        )
