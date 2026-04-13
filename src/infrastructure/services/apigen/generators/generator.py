import yaml
import json
from typing import Dict, Any

from .asyncapi_generator import AsyncAPIGenerator
from .graphql_generator import GraphQLGenerator
from src.infrastructure.services.generators.openapi_generator_service import OpenAPIGeneratorService


class GeneratorService:

    def transform_spec(self, content: str) -> str:
        """
        Main transformation function.
        Receives content in string/dict, identifies the specification type
        and returns the generated directory.
        """

        if not content:
            raise ValueError("No content received.")

        # If content is string, try to encode to bytes for detection or just use it
        if isinstance(content, str):
            raw_bytes = content.encode("utf-8")
        else:
            raw_bytes = content if isinstance(content, bytes) else str(content).encode("utf-8")

        content_str = content.decode('utf-8') if isinstance(content, bytes) else content

        spec_type = self._detect_spec_type(raw_bytes)
        if spec_type == "openapi":
            output_path = OpenAPIGeneratorService.generate(content_str)

        elif spec_type == "asyncapi":
            generator = AsyncAPIGenerator()
            output_path = generator.generate(content)
        elif spec_type == "graphql":
            generator = GraphQLGenerator()
            output_path = generator.generate(content)
        else:
            raise ValueError("Could not identify if the file is OpenAPI, AsyncAPI or GraphQL.")

        return output_path


    def _detect_spec_type(self, raw_bytes: bytes) -> str:
        txt = raw_bytes.decode("utf-8", errors="ignore").strip()
        first_char = txt[0] if txt else ""
        if first_char not in ["{", "[", "-"]:
            return "graphql"

        try:
            spec = json.loads(txt)
        except Exception:
            try:
                spec = yaml.safe_load(txt)
            except Exception:
                return "graphql"

        if isinstance(spec, dict):
            if "openapi" in spec:
                return "openapi"
            if "asyncapi" in spec:
                return "asyncapi"

        return "graphql"
