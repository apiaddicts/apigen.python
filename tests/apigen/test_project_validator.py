import pytest
import yaml
from src.infrastructure.services.apigen.validators.project_validator import ProjectValidator

@pytest.mark.asyncio
async def test_project_parameter_validator_valid(read_file):
    file = read_file("prueba/data-types-api.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)
    result = ProjectValidator().validate(spec)
    assert result is None

@pytest.mark.asyncio
async def test_project_parameter_validator_invalid(read_file):
    file = read_file("prueba/data-types-api-invalid-project.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)

    with pytest.raises(ValueError):
        ProjectValidator().validate(spec)
