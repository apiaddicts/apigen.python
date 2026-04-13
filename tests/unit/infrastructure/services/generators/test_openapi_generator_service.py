import base64
import json
import os
import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.services.generators.openapi_generator_service import OpenAPIGeneratorService


def _fake_generate_project(json_path, output_dir, **kwargs):
    """Create a minimal project directory so post-processing doesn't fail."""
    with open(json_path, "r") as f:
        data = json.load(f)
    slug = data.get("project", {}).get("name", "project").lower().replace(" ", "_").replace("-", "_")
    project_dir = os.path.join(output_dir, slug)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)


class TestOpenAPIGeneratorService:

    @pytest.fixture
    def valid_openapi_str(self):
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "x-apigen-project": {
                "name": "Test Project",
                "description": "Description",
                "version": "1.0.0",
                "data-driver": "postgresql"
            },
            "components": {
                "x-apigen-models": {
                    "User": {
                        "attributes": [],
                        "relational-persistence": {"table": "users"}
                    }
                },
                "schemas": {}
            },
            "paths": {}
        }
        return json.dumps(spec)

    @patch("src.infrastructure.services.apigen.generators.openapi_generator.apigen_copier")
    def test_generate_success(self, mock_copier, valid_openapi_str):
        mock_copier.generate_project = MagicMock(side_effect=_fake_generate_project)
        result = OpenAPIGeneratorService.generate(valid_openapi_str)

        assert isinstance(result, str)
        assert "openapi_project_" in result

    def test_generate_invalid_base64_ignored(self):
        invalid_input = "not-a-valid-json-string@@@"
        
        result = OpenAPIGeneratorService.generate(invalid_input)
        assert isinstance(result, dict)
        assert result["validation_results"].get("all_valid") is False

    def test_generate_invalid_spec_content(self):
        invalid_spec = "i am just text"

        result = OpenAPIGeneratorService.generate(invalid_spec)
        assert isinstance(result, dict)
        assert result["validation_results"].get("all_valid") is False
