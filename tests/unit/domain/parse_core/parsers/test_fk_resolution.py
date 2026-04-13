import os
import tempfile
import pytest
from unittest.mock import MagicMock
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser
from src.infrastructure.services.apigen.generators.openapi_generator import OpenAPIGenerator


class TestResolveResponseType:
    """Tests for _resolve_response_type: FK ID detection."""

    def _make_attr(self, name, type_, items_ref_model=None):
        attr = MagicMock()
        attr.name = name
        attr.type = type_
        attr.items_ref_model = items_ref_model
        return attr

    def test_fk_id_returns_long(self):
        parser = OpenAPIParser()
        attr = self._make_attr("category", "Relation")
        result = parser._resolve_response_type("categoryId", attr)
        assert result == "Long"

    def test_same_name_keeps_relation(self):
        """1:1 relation (no items_ref_model) stays as Relation."""
        parser = OpenAPIParser()
        attr = self._make_attr("category", "Relation")
        result = parser._resolve_response_type("category", attr)
        assert result == "Relation"

    def test_one_to_many_returns_array(self):
        """1:N relation (items_ref_model set) returns Array for List[X] generation."""
        parser = OpenAPIParser()
        attr = self._make_attr("visit", "Relation", items_ref_model="Visit")
        result = parser._resolve_response_type("visit", attr)
        assert result == "Array"

    def test_non_relation_unchanged(self):
        parser = OpenAPIParser()
        attr = self._make_attr("name", "String")
        result = parser._resolve_response_type("name", attr)
        assert result == "String"

    def test_different_name_non_relation_unchanged(self):
        parser = OpenAPIParser()
        attr = self._make_attr("status", "Integer")
        result = parser._resolve_response_type("statusCode", attr)
        assert result == "Integer"


class TestCompareResponses:
    """Tests for compare_responses: response code normalization."""

    def test_string_codes(self):
        parser = OpenAPIParser()
        responses = {"200": {}, "404": {}}
        result = parser.compare_responses(responses)
        assert str(result) == "200"

    def test_integer_codes(self):
        parser = OpenAPIParser()
        responses = {201: {}, 404: {}}
        result = parser.compare_responses(responses)
        assert str(result).startswith("2")

    def test_multiple_2xx_picks_lowest(self):
        parser = OpenAPIParser()
        responses = {"201": {}, "200": {}, "404": {}}
        result = parser.compare_responses(responses)
        assert str(result) == "200"

    def test_no_2xx_raises(self):
        parser = OpenAPIParser()
        responses = {"404": {}, "500": {}}
        with pytest.raises(AssertionError):
            parser.compare_responses(responses)


class TestMapRequestAttribute:
    """Tests for _map_request_attribute: graceful handling of unmapped attrs."""

    def test_direct_match(self):
        parser = OpenAPIParser()
        attr = MagicMock()
        entity_map = {"name": attr}
        result = parser._map_request_attribute("name", {}, entity_map, "Pet")
        assert result is attr

    def test_no_mapping_tag_returns_none(self):
        parser = OpenAPIParser()
        properties = {"unknownField": {"type": "string"}}
        result = parser._map_request_attribute(
            "unknownField", properties, {}, "Pet"
        )
        assert result is None

    def test_mapped_field_found(self):
        parser = OpenAPIParser()
        attr = MagicMock()
        properties = {
            "customName": {
                "x-apigen-mapping": {"field": "name"}
            }
        }
        entity_map = {"name": attr}
        result = parser._map_request_attribute(
            "customName", properties, entity_map, "Pet"
        )
        assert result is attr

    def test_dotted_field_resolves_root(self):
        parser = OpenAPIParser()
        attr = MagicMock()
        properties = {
            "categoryId": {
                "x-apigen-mapping": {"field": "category.id"}
            }
        }
        entity_map = {"category": attr}
        result = parser._map_request_attribute(
            "categoryId", properties, entity_map, "Pet"
        )
        assert result is attr

    def test_mapped_field_not_found_returns_none(self):
        parser = OpenAPIParser()
        properties = {
            "mystery": {
                "x-apigen-mapping": {"field": "nonexistent"}
            }
        }
        result = parser._map_request_attribute(
            "mystery", properties, {}, "Pet"
        )
        assert result is None


class TestMapResponseAttribute:
    """Tests for _map_response_attribute: graceful handling of unmapped attrs."""

    def test_direct_match(self):
        parser = OpenAPIParser()
        attr = MagicMock()
        entity_map = {"id": attr}
        result = parser._map_response_attribute("id", {}, entity_map, "Pet")
        assert result is attr

    def test_no_mapping_tag_returns_none(self):
        parser = OpenAPIParser()
        properties = {"extraField": {"type": "string"}}
        result = parser._map_response_attribute(
            "extraField", properties, {}, "Pet"
        )
        assert result is None

    def test_mapped_field_found(self):
        parser = OpenAPIParser()
        attr = MagicMock()
        properties = {
            "displayName": {
                "x-apigen-mapping": {"field": "name"}
            }
        }
        entity_map = {"name": attr}
        result = parser._map_response_attribute(
            "displayName", properties, entity_map, "Pet"
        )
        assert result is attr


class TestGetSchemaDefinitionByModelAndMethod:
    """Tests for schema lookup with method-specific and fallback matching."""

    def test_exact_method_match(self):
        parser = OpenAPIParser()
        parser.definition = {
            "components": {
                "schemas": {
                    "PetPost": {
                        "x-apigen-mapping": {"model": "Pet", "method": "post"},
                        "properties": {"name": {"type": "string"}}
                    },
                    "PetGet": {
                        "x-apigen-mapping": {"model": "Pet", "method": "get"},
                        "properties": {"id": {"type": "integer"}}
                    }
                }
            }
        }
        schema, name = parser.get_schema_definition_by_model_and_method("Pet", "post")
        assert name == "PetPost"
        assert "name" in schema["properties"]

    def test_fallback_to_no_method(self):
        parser = OpenAPIParser()
        parser.definition = {
            "components": {
                "schemas": {
                    "Pet": {
                        "x-apigen-mapping": {"model": "Pet"},
                        "properties": {"id": {"type": "integer"}}
                    }
                }
            }
        }
        schema, name = parser.get_schema_definition_by_model_and_method("Pet", "get")
        assert name == "Pet"
        assert schema is not None

    def test_no_match_returns_none(self):
        parser = OpenAPIParser()
        parser.definition = {
            "components": {
                "schemas": {
                    "Order": {
                        "x-apigen-mapping": {"model": "Order", "method": "post"},
                        "properties": {}
                    }
                }
            }
        }
        schema, name = parser.get_schema_definition_by_model_and_method("Pet", "get")
        assert schema is None
        assert name is None

    def test_method_match_preferred_over_fallback(self):
        parser = OpenAPIParser()
        parser.definition = {
            "components": {
                "schemas": {
                    "Pet": {
                        "x-apigen-mapping": {"model": "Pet"},
                        "properties": {"id": {"type": "integer"}}
                    },
                    "PetPost": {
                        "x-apigen-mapping": {"model": "Pet", "method": "post"},
                        "properties": {"name": {"type": "string"}}
                    }
                }
            }
        }
        schema, name = parser.get_schema_definition_by_model_and_method("Pet", "post")
        assert name == "PetPost"


class TestSnakeToCamel:
    """Tests for _snake_to_camel utility."""

    def test_simple(self):
        assert OpenAPIGenerator._snake_to_camel("category_id") == "categoryId"

    def test_multiple_parts(self):
        assert OpenAPIGenerator._snake_to_camel("user_first_name") == "userFirstName"

    def test_no_underscore(self):
        assert OpenAPIGenerator._snake_to_camel("name") == "name"

    def test_single_char_parts(self):
        assert OpenAPIGenerator._snake_to_camel("a_b_c") == "aBC"


class TestPatchDomainModel:
    """Tests for _patch_domain_model: FK ID field injection."""

    def test_adds_fk_field_after_relation(self):
        generator = OpenAPIGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            model_dir = os.path.join(tmpdir, "domain", "models", "pet")
            os.makedirs(model_dir)
            model_path = os.path.join(model_dir, "pet_model.py")

            with open(model_path, "w") as f:
                f.write(
                    "class Pet(BaseModel):\n"
                    "    id: Optional[int] = None\n"
                    "    category: Optional[Category] = None\n"
                    "    name: Optional[str] = None\n"
                )

            fk_list = [("categoryId", "category_id", "category")]
            generator._patch_domain_model(tmpdir, "pet", "Pet", fk_list)

            with open(model_path, "r") as f:
                content = f.read()

            assert "categoryId: Optional[int] = None" in content
            lines = content.split("\n")
            cat_idx = next(i for i, l in enumerate(lines) if "category: Optional" in l)
            fk_idx = next(i for i, l in enumerate(lines) if "categoryId: Optional[int]" in l)
            assert fk_idx > cat_idx

    def test_no_file_does_not_crash(self):
        generator = OpenAPIGenerator()
        generator._patch_domain_model("/nonexistent", "pet", "Pet", [("categoryId", "category_id", "category")])


class TestPatchMapper:
    """Tests for _patch_mapper: FK ID prioritization in mapper."""

    def test_patches_to_entity_mapping(self):
        generator = OpenAPIGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            mapper_dir = os.path.join(tmpdir, "infrastructure", "mappers", "pet")
            os.makedirs(mapper_dir)
            mapper_path = os.path.join(mapper_dir, "pet_mapper.py")

            with open(mapper_path, "w") as f:
                f.write(
                    "class PetMapper:\n"
                    "    @staticmethod\n"
                    "    def to_entity(model):\n"
                    "        return PetEntity(\n"
                    "            category_id=model.category.id if model.category else None,\n"
                    "        )\n"
                    "    @staticmethod\n"
                    "    def to_domain(entity):\n"
                    "        return Pet(\n"
                    "            category=entity.category,\n"
                    "        )\n"
                )

            fk_list = [("categoryId", "category_id", "category")]
            generator._patch_mapper(tmpdir, "pet", "Pet", fk_list)

            with open(mapper_path, "r") as f:
                content = f.read()

            assert "model.categoryId if model.categoryId is not None" in content
            assert "categoryId=entity.category_id," in content

    def test_no_file_does_not_crash(self):
        generator = OpenAPIGenerator()
        generator._patch_mapper("/nonexistent", "pet", "Pet", [("categoryId", "category_id", "category")])


class TestNormalizeResponseCodes:
    """Tests for _normalize_response_codes in OpenAPIParserService."""

    def test_integer_keys_converted(self):
        from src.infrastructure.services.validators.openapi_parser_service import OpenAPIParserService
        service = OpenAPIParserService.__new__(OpenAPIParserService)
        service.spec_dict = {
            "paths": {
                "/pets": {
                    "get": {
                        "responses": {
                            200: {"description": "OK"},
                            404: {"description": "Not found"},
                        }
                    }
                }
            }
        }
        service._normalize_response_codes()
        responses = service.spec_dict["paths"]["/pets"]["get"]["responses"]
        assert "200" in responses
        assert "404" in responses
        assert 200 not in responses

    def test_string_keys_unchanged(self):
        from src.infrastructure.services.validators.openapi_parser_service import OpenAPIParserService
        service = OpenAPIParserService.__new__(OpenAPIParserService)
        service.spec_dict = {
            "paths": {
                "/pets": {
                    "get": {
                        "responses": {
                            "200": {"description": "OK"},
                        }
                    }
                }
            }
        }
        service._normalize_response_codes()
        responses = service.spec_dict["paths"]["/pets"]["get"]["responses"]
        assert "200" in responses
