import io
import pytest
import base64
from fastapi import UploadFile
from src.infrastructure.services.apigen.generators.graphql_generator import GraphQLGenerator

@pytest.mark.asyncio
async def test_graphql_generator_valid(read_file):
    file = read_file("prueba/valid.graphql")
    upload_file = UploadFile(filename="valid.graphql", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    generator = GraphQLGenerator()
    result = generator.generate(content_str)
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_graphql_generator_invalid_sintax(read_file):
    file = read_file("prueba/invalid_sintax.graphql")
    upload_file = UploadFile(filename="valid.graphql", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    generator = GraphQLGenerator()
    result = generator.generate(content_str)
    assert isinstance(result, dict)
    assert result["all_valid"] is False

@pytest.mark.asyncio
async def test_graphql_generator_invalid_project(read_file):
    file = read_file("prueba/invalid_project.graphql")
    upload_file = UploadFile(filename="valid.graphql", file=io.BytesIO(file))
    content = await upload_file.read()
    content_str = content.decode("utf-8")

    generator = GraphQLGenerator()
    result = generator.generate(content_str)
    assert isinstance(result, dict)
    assert result["all_valid"] is False
