import pytest
import yaml
from src.infrastructure.services.apigen.validators.path_binding_validator import PathBindingValidator

@pytest.mark.asyncio
async def test_path_binding_parameter_validator_valid(read_file):
    file = read_file("prueba/data-types-api.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)
    result = PathBindingValidator().validate(spec, ['EntityTypes'])
    assert result is None

@pytest.mark.asyncio
async def test_path_binding_parameter_validator_invalid(read_file):
    file = read_file("prueba/data-types-api-invalid-binding.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)

    with pytest.raises(ValueError):
        PathBindingValidator().validate(spec, ['EntityTypes'])
