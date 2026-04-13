"""Tests for SpringBoot-style model normalization.

Verifies that type=ModelName (SpringBoot format) produces the same internal
representation as type=Relation + ref-model=ModelName (Python format).
Both formats must be accepted and generate identical downstream results.
"""
from src.domain.parse_core.schemas.entity_schema import (
    EntityAttribute,
    EntityAttrubuteColumnProperties,
)
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser


class TestSpringBootStyleNormalization:
    """type=ModelName is normalized to type=Relation + ref_model=ModelName."""

    def test_model_name_becomes_relation(self):
        """type: Categories → type=Relation, ref_model=Categories."""
        attr = EntityAttribute(**{
            "name": "category",
            "type": "Categories",
            "relational-persistence": {"column": "category_id"},
        })
        assert attr.type == "Relation"
        assert attr.ref_model == "Categories"

    def test_explicit_relation_unchanged(self):
        """type: Relation with ref-model stays unchanged (retrocompatible)."""
        attr = EntityAttribute(**{
            "name": "category",
            "type": "Relation",
            "ref-model": "Categories",
            "relational-persistence": {"column": "category_id"},
        })
        assert attr.type == "Relation"
        assert attr.ref_model == "Categories"

    def test_basic_types_not_converted(self):
        """Basic types (String, Integer, etc.) must NOT be treated as model names."""
        for basic_type in ["String", "Integer", "Long", "Boolean", "Float",
                           "Double", "LocalDate", "LocalDateTime", "Date"]:
            attr = EntityAttribute(**{
                "name": "field",
                "type": basic_type,
            })
            assert attr.type == basic_type, f"{basic_type} should not be converted to Relation"
            assert attr.ref_model is None

    def test_ref_model_not_overwritten_if_already_set(self):
        """If ref-model is already set, type=ModelName still normalizes but keeps existing ref_model."""
        attr = EntityAttribute(**{
            "name": "category",
            "type": "Cat",
            "ref-model": "Categories",
            "relational-persistence": {"column": "category_id"},
        })
        assert attr.type == "Relation"
        assert attr.ref_model == "Categories", "Explicit ref-model should not be overwritten"


class TestSpringBootArrayRelations:
    """Array relations with items-type=ModelName."""

    def test_array_items_type_model_name(self):
        """is-array: true + items-type: Pet → items_ref_model=Pet."""
        attr = EntityAttribute(**{
            "name": "pets",
            "type": "Array",
            "is-array": True,
            "items-type": "Pet",
            "relational-persistence": {"foreign-column": "owner_id"},
        })
        assert attr.is_array is True
        assert attr.items_ref_model == "Pet"

    def test_array_items_type_basic_type_not_converted(self):
        """is-array: true + items-type: String → items_ref_model stays None."""
        attr = EntityAttribute(**{
            "name": "tags",
            "type": "Array",
            "is-array": True,
            "items-type": "String",
        })
        assert attr.is_array is True
        assert attr.items_ref_model is None

    def test_array_ref_model_propagates(self):
        """is-array + ref_model (Python style) still propagates to items_ref_model."""
        attr = EntityAttribute(**{
            "name": "pets",
            "type": "Array",
            "is-array": True,
            "ref-model": "Pet",
            "relational-persistence": {"foreign-column": "owner_id"},
        })
        assert attr.items_ref_model == "Pet"


class TestSpringBootAndPythonProduceSameResult:
    """Both formats produce identical internal representation."""

    def test_many_to_one_equivalence(self):
        """SpringBoot vs Python format for ManyToOne produce same result."""
        springboot = EntityAttribute(**{
            "name": "category",
            "type": "Categories",
            "relational-persistence": {"column": "category_id", "join-column": "id"},
        })
        python_style = EntityAttribute(**{
            "name": "category",
            "type": "Relation",
            "ref-model": "Categories",
            "relational-persistence": {"column": "category_id", "join-column": "id"},
        })
        assert springboot.type == python_style.type
        assert springboot.ref_model == python_style.ref_model
        assert springboot.is_array == python_style.is_array

    def test_one_to_many_equivalence(self):
        """SpringBoot vs Python format for OneToMany produce same result."""
        springboot = EntityAttribute(**{
            "name": "pets",
            "type": "Array",
            "is-array": True,
            "items-type": "Pet",
            "relational-persistence": {"foreign-column": "owner_id"},
        })
        python_style = EntityAttribute(**{
            "name": "pets",
            "type": "Array",
            "is-array": True,
            "items-ref-model": "Pet",
            "relational-persistence": {"foreign-column": "owner_id"},
        })
        assert springboot.items_ref_model == python_style.items_ref_model
        assert springboot.is_array == python_style.is_array

    def test_many_to_many_equivalence(self):
        """SpringBoot vs Python format for ManyToMany produce same result."""
        springboot = EntityAttribute(**{
            "name": "tags",
            "type": "Array",
            "is-array": True,
            "items-type": "Tag",
            "relational-persistence": {
                "join-table": "pet_tags",
                "join-column": "pet_id",
                "inverse-join-column": "tag_id",
            },
        })
        python_style = EntityAttribute(**{
            "name": "tags",
            "type": "Array",
            "is-array": True,
            "items-ref-model": "Tag",
            "relational-persistence": {
                "join-table": "pet_tags",
                "join-column": "pet_id",
                "inverse-join-column": "tag_id",
            },
        })
        assert springboot.items_ref_model == python_style.items_ref_model
        assert springboot.is_array == python_style.is_array


class TestRelationTypeInference:
    """relation_type is inferred when not explicitly set."""

    def _make_parser_with_entities(self, entities_dict):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        parser = OpenAPIParser()
        parser.entities = entities_dict
        parser._infer_relation_types()
        return parser

    def test_infer_many_to_one(self):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="pets", attributes=[
            EntityAttribute(**{
                "name": "category", "type": "Relation", "ref-model": "Categories",
                "relational-persistence": {"column": "category_id"},
            }),
        ])
        self._make_parser_with_entities({"Pet": entity})
        attr = entity.attributes[0]
        assert attr.column_properties.relation_type == "ManyToOne"

    def test_infer_one_to_many(self):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="owners", attributes=[
            EntityAttribute(**{
                "name": "pets", "type": "Array", "is-array": True,
                "items-ref-model": "Pet",
                "relational-persistence": {"foreign-column": "owner_id"},
            }),
        ])
        self._make_parser_with_entities({"Owner": entity})
        attr = entity.attributes[0]
        assert attr.column_properties.relation_type == "OneToMany"

    def test_infer_many_to_many(self):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="pets", attributes=[
            EntityAttribute(**{
                "name": "tags", "type": "Array", "is-array": True,
                "items-ref-model": "Tag",
                "relational-persistence": {
                    "join-table": "pet_tags",
                    "join-column": "pet_id",
                    "inverse-join-column": "tag_id",
                },
            }),
        ])
        self._make_parser_with_entities({"Pet": entity})
        attr = entity.attributes[0]
        assert attr.column_properties.relation_type == "ManyToMany"

    def test_infer_one_to_one_inverse(self):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="users", attributes=[
            EntityAttribute(**{
                "name": "profile", "type": "Relation", "ref-model": "Profile",
                "relational-persistence": {"foreign-column": "user_id"},
            }),
        ])
        self._make_parser_with_entities({"User": entity})
        attr = entity.attributes[0]
        assert attr.column_properties.relation_type == "OneToOne"

    def test_explicit_relation_type_not_overridden(self):
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="pets", attributes=[
            EntityAttribute(**{
                "name": "category", "type": "Relation", "ref-model": "Categories",
                "relational-persistence": {
                    "column": "category_id",
                    "relation-type": "OneToOne",
                },
            }),
        ])
        self._make_parser_with_entities({"Pet": entity})
        attr = entity.attributes[0]
        assert attr.column_properties.relation_type == "OneToOne", \
            "Explicit relation-type should not be overridden by inference"

    def test_springboot_format_with_inference(self):
        """SpringBoot format (type=ModelName) + relation_type inference together."""
        from src.domain.parse_core.schemas.entity_schema import EntitySchema
        entity = EntitySchema(table="pets", attributes=[
            EntityAttribute(**{
                "name": "category",
                "type": "Categories",  # SpringBoot style
                "relational-persistence": {"column": "category_id"},
            }),
        ])
        self._make_parser_with_entities({"Pet": entity})
        attr = entity.attributes[0]
        assert attr.type == "Relation"
        assert attr.ref_model == "Categories"
        assert attr.column_properties.relation_type == "ManyToOne"
