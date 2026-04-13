import pytest
import yaml
from src.infrastructure.services.apigen.validators.mapping_validator import MappingValidator

@pytest.mark.asyncio
async def test_mapping_parameter_validator_valid(read_file):
    file = read_file("prueba/data-types-api.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)
    result = MappingValidator().validate(spec, ['EntityTypes'])
    assert result is None

@pytest.mark.asyncio
async def test_mapping_parameter_validator_invalid(read_file):
    file = read_file("prueba/data-types-api-invalid-mapping.yaml")
    content_str = file.decode("utf-8")
    spec = yaml.safe_load(content_str)

    with pytest.raises(ValueError) as exc:
        MappingValidator().validate(spec, ['EntityTypes'])

    assert "EntityTypes" in str(exc.value)
