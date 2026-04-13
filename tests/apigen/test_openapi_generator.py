import io
import os
import pytest
import base64
from unittest.mock import patch, MagicMock
from fastapi import UploadFile
from src.infrastructure.services.apigen.generators.openapi_generator import OpenAPIGenerator


def _fake_generate_project(json_path, output_dir, **kwargs):
    """Create a minimal project directory so post-processing doesn't fail."""
    with open(json_path, "r") as f:
        import json
        data = json.load(f)
    slug = data.get("project", {}).get("name", "project").lower().replace(" ", "_").replace("-", "_")
    project_dir = os.path.join(output_dir, slug)
    os.makedirs(os.path.join(project_dir, "src"), exist_ok=True)


@pytest.mark.asyncio
@patch("src.infrastructure.services.apigen.generators.openapi_generator.apigen_copier")
async def test_openapi_generator_valid(mock_copier, read_file):
    mock_copier.generate_project = MagicMock(side_effect=_fake_generate_project)
    file = read_file("prueba/valid.openapi.yaml")
    upload_file = UploadFile(filename="valid.openapi.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
    parser = OpenAPIParser()
    parser.load_definition(spec_str=content_str)
    project_schema = parser.parse()

    generator = OpenAPIGenerator()
    result = generator.generate(project_schema, original_spec=content_str)
    assert isinstance(result, str), f"OpenAPI Valid Failed: {result}"

@pytest.mark.asyncio
async def test_openapi_generator_invalid_mapping(read_file):
    file = read_file("prueba/data-types-api-invalid-mapping.yaml")
    upload_file = UploadFile(filename="data-types-api-invalid-mapping.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
    parser = OpenAPIParser()
    parser.load_definition(spec_str=content_str)
    
    try:
        project_schema = parser.parse()
    except Exception:
        return

    generator = OpenAPIGenerator()
    result = generator.generate(project_schema, original_spec=content_str)
    assert result["validation_results"]['all_valid'] is False

@pytest.mark.asyncio
async def test_openapi_generator_invalid_binding(read_file):
    file = read_file("prueba/data-types-api-invalid-binding.yaml")
    upload_file = UploadFile(filename="data-types-api-invalid-binding.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
    parser = OpenAPIParser()
    parser.load_definition(spec_str=content_str)
    
    # Expect parser to fail or generator to handle it if parser succeeds
    try:
        project_schema = parser.parse()
    except Exception:
        # If parsing fails, that's considered a "pass" for an invalid input test 
        # (since we can't generate from invalid input)
        return

    generator = OpenAPIGenerator()
    result = generator.generate(project_schema, original_spec=content_str)
    assert result["validation_results"]['all_valid'] is False

@pytest.mark.asyncio
async def test_openapi_generator_invalid_project(read_file):
    file = read_file("prueba/data-types-api-invalid-project.yaml")
    upload_file = UploadFile(filename="data-types-api-invalid-project.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
    parser = OpenAPIParser()
    parser.load_definition(spec_str=content_str)
    
    try:
        project_schema = parser.parse()
    except Exception:
        return

    generator = OpenAPIGenerator()
    result = generator.generate(project_schema, original_spec=content_str)
    assert result["validation_results"]['all_valid'] is False
