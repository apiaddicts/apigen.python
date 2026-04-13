import io
import pytest
import base64
from fastapi import UploadFile
from src.infrastructure.services.apigen.generators.asyncapi_generator import AsyncAPIGenerator



@pytest.mark.asyncio
async def test_asyncapi_generator_invalid_project_param(read_file):
    file = read_file("prueba/invalid_project_param_asyncapi.yaml")
    upload_file = UploadFile(filename="invalid_project_param_asyncapi.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    generator = AsyncAPIGenerator()
    result = generator.generate(content_str)
    assert isinstance(result, dict)
    assert result['all_valid'] is False

@pytest.mark.asyncio
async def test_asyncapi_generator_invalid_binding_param(read_file):
    file = read_file("prueba/invalid_binding_param_asyncapi.yaml")
    upload_file = UploadFile(filename="invalid_binding_param_asyncapi.yaml", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    generator = AsyncAPIGenerator()
    result = generator.generate(content_str)
    assert isinstance(result, dict)
    assert result['all_valid'] is False
