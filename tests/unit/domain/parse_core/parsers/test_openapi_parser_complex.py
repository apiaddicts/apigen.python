from unittest.mock import MagicMock
import pytest
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser

class TestOpenAPIParserComplex:
    def test_resolve_schema_properties_simple(self):
        parser = OpenAPIParser()
        schema = {
            "properties": {
                "prop1": {"type": "string"}
            }
        }
        props = parser._resolve_schema_properties(schema)
        assert "prop1" in props
        assert props["prop1"]["type"] == "string"

    def test_resolve_schema_properties_allof(self):
        parser = OpenAPIParser()
        schema = {
            "allOf": [
                {
                    "properties": {
                        "parent_prop": {"type": "integer"}
                    }
                },
                {
                    "properties": {
                        "child_prop": {"type": "string"}
                    }
                }
            ]
        }
        props = parser._resolve_schema_properties(schema)
        assert "parent_prop" in props
        assert "child_prop" in props
        assert props["parent_prop"]["type"] == "integer"
        assert props["child_prop"]["type"] == "string"

    def test_resolve_schema_properties_nested_allof(self):
        parser = OpenAPIParser()
        schema = {
            "allOf": [
                {
                    "allOf": [
                        {
                            "properties": {
                                "grandparent_prop": {"type": "boolean"}
                            }
                        }
                    ]
                },
                {
                    "properties": {
                        "child_prop": {"type": "string"}
                    }
                }
            ]
        }
        props = parser._resolve_schema_properties(schema)
        assert "grandparent_prop" in props
        assert "child_prop" in props

    def test_resolve_schema_properties_oneof_merged(self):
        parser = OpenAPIParser()
        schema = {
            "oneOf": [
                {
                    "properties": {
                        "option_a": {"type": "string"}
                    }
                },
                {
                    "properties": {
                        "option_b": {"type": "integer"}
                    }
                }
            ]
        }
        props = parser._resolve_schema_properties(schema)
        assert "option_a" in props
        assert "option_b" in props

    def test_resolve_schema_properties_mixed(self):
        parser = OpenAPIParser()
        schema = {
            "properties": {
                "base_prop": {"type": "string"}
            },
            "allOf": [
                {
                    "properties": {
                        "mixed_prop": {"type": "integer"}
                    }
                }
            ]
        }
        props = parser._resolve_schema_properties(schema)
        assert "base_prop" in props
        assert "mixed_prop" in props


class TestPrefixUrlStripping:
    """ISSUE-018: Full URLs in servers.url must be stripped to path only."""

    def _parse_prefix(self, server_url):
        import yaml
        spec = {
            "openapi": "3.0.0",
            "x-apigen-project": {
                "name": "PrefixTest", "version": "1.0.0",
                "description": "t", "data-driver": "postgresql",
            },
            "servers": [{"url": server_url}],
            "x-apigen-models": {},
            "components": {"schemas": {}},
            "paths": {},
        }
        parser = OpenAPIParser()
        parser.load_definition(spec_str=yaml.dump(spec))
        parser.get_project()
        return parser.project.prefix

    def test_full_url_stripped_to_path(self):
        assert self._parse_prefix("https://petstore3.example.io/api/v3") == "/api/v3"

    def test_path_only_unchanged(self):
        assert self._parse_prefix("/api/v3") == "/api/v3"

    def test_trailing_slash_removed(self):
        assert self._parse_prefix("https://example.com/api/v3/") == "/api/v3"

    def test_empty_path_no_prefix(self):
        assert self._parse_prefix("/") == ""

