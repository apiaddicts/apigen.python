import logging
import yaml
import base64
import re
from typing import Dict, Any
from openapi_spec_validator import validate as openapi_validate, openapi_v30_spec_validator
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from src.infrastructure.services.validators.base_spec_parser_service import BaseSpecParserService

logger = logging.getLogger(__name__)

class OpenAPIParserService(BaseSpecParserService):
    def _get_spec_name(self) -> str:
        return "OpenAPI"

    def _normalize_response_codes(self):
        """Convert integer response codes to strings in spec_dict (YAML parses 200 as int)."""
        paths = self.spec_dict.get('paths', {})
        for path in paths.values():
            for method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'):
                operation = path.get(method)
                if operation and 'responses' in operation:
                    responses = operation['responses']
                    int_keys = [k for k in responses if isinstance(k, int)]
                    for k in int_keys:
                        responses[str(k)] = responses.pop(k)

    def _validate_spec(self, file_path: str) -> Dict[str, Any]:
        errors = []
        openapi_version = self.spec_dict.get('openapi', '') or self.spec_dict.get('swagger', '')
        title = self.spec_dict.get('info', {}).get('title')

        self._normalize_response_codes()

        try:
            raw_errors = list(openapi_v30_spec_validator.iter_errors(self.spec_dict))
            if raw_errors:
                clean_errors = []
                for err in raw_errors:
                    simple = err.message
                    clean_errors.append(simple)
                raise ValueError({
                    "is_valid": False,
                    "message": clean_errors
                })
            logger.info("Especificación OpenAPI validada exitosamente")
        except OpenAPIValidationError as e:
            logger.warning(f"Error de validación OpenAPI: {str(e)}")
            errors.append(str(e))
        except ValueError as e:
            payload = e.args[0]
            logger.error(f"validación OpenAPI: {payload.get('message')}")
            errors = payload.get('message')
        except Exception as e:
            logger.error(f"Error inesperado durante validación OpenAPI: {str(e)}")
            errors.append(f"Error inesperado: {str(e)}")

        if errors:
            return {
                "valid": False,
                "version": openapi_version if openapi_version else None,
                "title": title,
                "errors": errors
            }

        yaml_content = yaml.dump(self.spec_dict, default_flow_style=False, allow_unicode=True)
        
        return {
            "valid": True,
            "version": openapi_version,
            "title": title,
            "content": yaml_content,
            "errors": []
        }
