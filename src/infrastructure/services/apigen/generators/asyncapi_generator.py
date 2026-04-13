import tempfile
import yaml
import json
import logging
from typing import Dict, Any, Union

from ..validators.detailed_config_validator import DetailedConfigValidator
from src.domain.parse_core.parsers.asyncapi_parser import AsyncAPIParser

try:
    from apigen_copier import generate_async_project
    HAS_APIGEN_COPIER = True
except ImportError:
    HAS_APIGEN_COPIER = False

logger = logging.getLogger(__name__)


class AsyncAPIGenerator:

    def generate(self, content: Union[str, dict], existing_project_dir: str = None) -> Union[str, Dict[str, Any]]:
        if isinstance(content, dict):
            spec = content
        else:
            spec = self._parse_spec(content.encode('utf-8') if isinstance(content, str) else content)
        self._validate_asyncapi(spec)

        validation_result = DetailedConfigValidator.validate_asyncapi(spec)
        if not validation_result["all_valid"]:
            return validation_result

        if not HAS_APIGEN_COPIER:
            raise ImportError(
                "apigen_copier package is not installed. Cannot generate AsyncAPI project. "
                "Please install it (e.g. pip install ../ods-data-generator-examples)"
            )


        parser = AsyncAPIParser()
        parser.load_definition(spec)
        parsed_schema = parser.parse()


        parsed_data = parsed_schema.model_dump(by_alias=True)


        output_dir = tempfile.mkdtemp(prefix="asyncapi_project_")
        with open(f"{output_dir}/project.json", "w") as f:
            json.dump(parsed_data, f, indent=2)


        generate_async_project(
            parsed_data,
            output_dir,
            existing_project_dir=existing_project_dir,
        )
        logger.info(f"AsyncAPI project generated at {output_dir}")

        return output_dir

    def _parse_spec(self, raw_bytes: bytes):
        txt = raw_bytes.decode("utf-8")
        try:
            return json.loads(txt)
        except Exception:
            pass
        try:
            return yaml.safe_load(txt)
        except Exception:
            raise ValueError("La especificación AsyncAPI no es JSON ni YAML válido.")

    def _validate_asyncapi(self, spec: dict):
        if "asyncapi" not in spec:
            raise ValueError("El archivo no contiene el campo obligatorio 'asyncapi'.")
        if "channels" not in spec:
            raise ValueError("AsyncAPI: falta el bloque 'channels'.")
