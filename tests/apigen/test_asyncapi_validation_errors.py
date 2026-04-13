"""
Tests for AsyncAPI validation error handling improvements.
- Missing x-apigen-models should produce a clear error
- CLI errors should be parsed individually, not as a blob
- NODE_ENV noise should be filtered out
"""
import pytest
import yaml
from unittest.mock import patch, MagicMock
from src.infrastructure.services.apigen.generators.asyncapi_generator import AsyncAPIGenerator
from src.infrastructure.services.validators.asyncapi_parser_service import AsyncAPIParserService


# ── x-apigen-models required ───────────────────────────────────────

SPEC_WITHOUT_APIGEN = {
    "asyncapi": "3.0.0",
    "info": {"title": "Test", "version": "1.0.0"},
    "channels": {
        "testQueue": {
            "address": "test",
            "messages": {"TestMsg": {"payload": {"type": "string"}}}
        }
    },
    "operations": {
        "receiveTest": {
            "action": "receive",
            "channel": {"$ref": "#/channels/testQueue"},
            "messages": [{"$ref": "#/channels/testQueue/messages/TestMsg"}]
        }
    },
    "components": {
        "messages": {
            "TestMsg": {"payload": {"type": "string"}}
        }
    }
}


def test_generator_rejects_missing_apigen_models():
    """Spec without x-apigen-models should return all_valid=False with clear error."""
    generator = AsyncAPIGenerator()
    yaml_content = yaml.dump(SPEC_WITHOUT_APIGEN)
    result = generator.generate(yaml_content)

    assert isinstance(result, dict), f"Expected error dict, got {type(result)}"
    assert result["all_valid"] is False
    assert "x-apigen-models" in result["validations"]
    error = result["validations"]["x-apigen-models"]["error"]
    assert error is not None
    assert "x-apigen-models" in error


# ── CLI error parsing ──────────────────────────────────────────────

class TestCLIErrorParsing:

    def test_parse_structured_errors(self):
        """CLI output with error lines should be parsed into individual messages."""
        cli_output = (
            "File /tmp/test.yaml and/or referenced documents have governance issues.\n"
            "Errors \n"
            "/tmp/test.yaml\n"
            '  16:9  error  asyncapi-document-resolved  "0" property must have required property "type"  servers.production.security[0]\n'
            "  68:9  error  asyncapi3-operation-messages-from-referred-channel  Operation message does not belong to the specified channel.  operations.receiveImageUrl.messages[0]\n"
            "  84:14  error  asyncapi-document-resolved  Property \"schema\" is not expected to be here  components.messages.ImageUrlMessage.schema\n"
            "\n"
            "✖ 3 problems (3 errors, 0 warnings, 0 infos, 0 hints)\n"
        )
        parser = AsyncAPIParserService()
        errors = parser._parse_cli_errors(cli_output)

        assert len(errors) == 3
        assert "Line 16:9" in errors[0]
        assert "servers.production.security[0]" in errors[0]
        assert "Line 68:9" in errors[1]
        assert "operations.receiveImageUrl" in errors[1]
        assert "Line 84:14" in errors[2]
        assert "schema" in errors[2]

    def test_node_env_noise_filtered(self):
        """NODE_ENV and node-config noise should be filtered out."""
        cli_output = (
            "FATAL: NODE_ENV value of 'production' did not match any deployment config file names.\n"
            "FATAL: See https://github.com/node-config/node-config/wiki/Strict-Mode\n"
            "\n"
            "File /tmp/test.yaml and/or referenced documents have governance issues.\n"
            "Errors \n"
            "/tmp/test.yaml\n"
            '  16:9  error  asyncapi-document-resolved  "0" property must have required property "type"  servers.production.security[0]\n'
            "\n"
            "✖ 1 problems (1 errors, 0 warnings, 0 infos, 0 hints)\n"
        )
        parser = AsyncAPIParserService()
        errors = parser._parse_cli_errors(cli_output)

        assert len(errors) == 1
        assert "NODE_ENV" not in errors[0]
        assert "Line 16:9" in errors[0]

    def test_empty_output_returns_empty(self):
        """Empty or unparseable CLI output should return empty list."""
        parser = AsyncAPIParserService()
        assert parser._parse_cli_errors("") == []
        assert parser._parse_cli_errors("some random text") == []
