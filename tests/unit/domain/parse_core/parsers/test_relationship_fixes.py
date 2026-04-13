"""Regression tests for relationship generation fixes (ISSUE-009, 010, 011).

These tests validate that the parser correctly handles:
- ISSUE-009: ref_model is preserved from x-apigen-models (not overwritten by $ref)
- ISSUE-010: Join table entities get composite PK on FK columns
- ISSUE-011: ref_model propagates to response attributes for route templates
"""
import os
import pytest
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser


SPEC_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "..", "prueba", "apirest-funcional.yaml"
)


@pytest.fixture(scope="module")
def parsed_schema():
    """Parse apirest-funcional.yaml and return the schema."""
    if not os.path.exists(SPEC_PATH):
        pytest.skip("apirest-funcional.yaml not found")
    parser = OpenAPIParser()
    with open(SPEC_PATH) as f:
        parser.load_definition(spec_str=f.read())
    return parser.parse()


class TestRefModelPreservation:
    """ISSUE-009/011 regression: ref_model from x-apigen-models must not be overwritten."""

    def test_category_ref_model_is_entity_key(self, parsed_schema):
        """Pet.category ref_model should be 'Categories' (entity key), not 'Category' ($ref name)."""
        pet = parsed_schema.entities.get("Pet")
        assert pet is not None, "Pet entity not found"
        cat_attr = next((a for a in pet.attributes if a.name == "category"), None)
        assert cat_attr is not None, "Pet.category attribute not found"
        assert cat_attr.ref_model == "Categories", \
            f"ref_model should be 'Categories' (from x-apigen-models), got '{cat_attr.ref_model}'"

    def test_ref_model_in_response_attributes(self, parsed_schema):
        """Response attributes with type=Relation must carry ref_model for template lookups."""
        pet_router = parsed_schema.routers.get("pet")
        assert pet_router is not None, "Pet router not found"
        # Find GET endpoint with response
        for endpoint in pet_router.endpoints:
            if endpoint.response and endpoint.response.attributes:
                relation_attrs = [a for a in endpoint.response.attributes if a.type == "Relation"]
                for attr in relation_attrs:
                    assert attr.ref_model is not None, \
                        f"Response attribute '{attr.name}' missing ref_model"
                break


class TestJoinTableCompositePK:
    """ISSUE-010 regression: join table entities must have composite PK on FK columns."""

    def test_join_table_has_primary_keys(self, parsed_schema):
        """PetsTags entity FK columns should have primary_key=True after parsing."""
        pets_tags = parsed_schema.entities.get("PetsTags")
        assert pets_tags is not None, "PetsTags entity not found"
        pk_attrs = [
            a for a in pets_tags.attributes
            if a.column_properties and a.column_properties.primary_key
        ]
        assert len(pk_attrs) >= 2, \
            f"Expected 2+ composite PK columns in PetsTags, got {len(pk_attrs)}"

    def test_join_table_pk_columns_are_fk_relations(self, parsed_schema):
        """All PK columns in PetsTags should be FK relation columns."""
        pets_tags = parsed_schema.entities.get("PetsTags")
        assert pets_tags is not None
        for attr in pets_tags.attributes:
            if attr.column_properties and attr.column_properties.primary_key:
                assert attr.type == "Relation", \
                    f"PK column '{attr.name}' should be a Relation type"

    def test_normal_entity_pk_not_affected(self, parsed_schema):
        """Entities with an existing PK (like Pet) must not get extra PKs."""
        pet = parsed_schema.entities.get("Pet")
        assert pet is not None
        pk_attrs = [
            a for a in pet.attributes
            if a.column_properties and a.column_properties.primary_key
        ]
        assert len(pk_attrs) == 1, \
            f"Pet should have exactly 1 PK (id), got {len(pk_attrs)}"
        assert pk_attrs[0].name == "id"


class TestEnsureJoinTablePksUnit:
    """Unit test for _ensure_join_table_pks with synthetic data."""

    def test_adds_pk_to_all_relation_entity(self):
        """Entity with 2+ FK relations and no PK → composite PK added."""
        parser = OpenAPIParser()
        # Build a minimal join table entity via the parser's internal structures
        from src.domain.parse_core.schemas.entity_schema import EntitySchema, EntityAttribute, EntityAttrubuteColumnProperties
        join_entity = EntitySchema(
            table="student_courses",
            attributes=[
                EntityAttribute(**{
                    "name": "student", "type": "Relation",
                    "relational-persistence": {"column": "student_id", "foreign-column": "id"},
                }),
                EntityAttribute(**{
                    "name": "course", "type": "Relation",
                    "relational-persistence": {"column": "course_id", "foreign-column": "id"},
                }),
            ]
        )
        parser.entities = {"StudentCourses": join_entity}
        parser._ensure_join_table_pks()

        for attr in join_entity.attributes:
            assert attr.column_properties.primary_key, \
                f"FK column '{attr.name}' should have primary_key=True after _ensure_join_table_pks"

    def test_skips_entity_with_existing_pk(self):
        """Entity with an existing PK should not be modified."""
        parser = OpenAPIParser()
        from src.domain.parse_core.schemas.entity_schema import EntitySchema, EntityAttribute
        normal_entity = EntitySchema(
            table="pets",
            attributes=[
                EntityAttribute(**{
                    "name": "id", "type": "Long",
                    "relational-persistence": {"column": "id", "primary-key": True},
                }),
                EntityAttribute(**{
                    "name": "category", "type": "Relation",
                    "relational-persistence": {"column": "category_id", "foreign-column": "id"},
                }),
                EntityAttribute(**{
                    "name": "owner", "type": "Relation",
                    "relational-persistence": {"column": "owner_id", "foreign-column": "id"},
                }),
            ]
        )
        parser.entities = {"Pet": normal_entity}
        parser._ensure_join_table_pks()

        # category and owner should NOT become PKs
        cat = next(a for a in normal_entity.attributes if a.name == "category")
        assert not cat.column_properties.primary_key, \
            "category FK should NOT get primary_key when entity already has a PK"

    def test_join_table_with_extra_fields(self):
        """Join table with metadata fields — only FK relations get PK, extra fields untouched."""
        parser = OpenAPIParser()
        from src.domain.parse_core.schemas.entity_schema import EntitySchema, EntityAttribute
        join_entity = EntitySchema(
            table="student_courses",
            attributes=[
                EntityAttribute(**{
                    "name": "student", "type": "Relation",
                    "relational-persistence": {"column": "student_id", "foreign-column": "id"},
                }),
                EntityAttribute(**{
                    "name": "course", "type": "Relation",
                    "relational-persistence": {"column": "course_id", "foreign-column": "id"},
                }),
                EntityAttribute(**{
                    "name": "enrollmentDate", "type": "Date",
                    "relational-persistence": {"column": "enrollment_date"},
                }),
            ]
        )
        parser.entities = {"StudentCourses": join_entity}
        parser._ensure_join_table_pks()

        student = next(a for a in join_entity.attributes if a.name == "student")
        course = next(a for a in join_entity.attributes if a.name == "course")
        date_attr = next(a for a in join_entity.attributes if a.name == "enrollmentDate")
        assert student.column_properties.primary_key, "student FK should be PK"
        assert course.column_properties.primary_key, "course FK should be PK"
        assert not date_attr.column_properties.primary_key, "enrollmentDate should NOT be PK"


class TestPrimitiveResponseDetection:
    """ISSUE-015 regression: primitive responses (type: string) should not get entity model."""

    def test_login_user_no_response_class(self, parsed_schema):
        """loginUser returns type: string — response_class_name should be None."""
        user_router = parsed_schema.routers.get("user")
        assert user_router is not None, "User router not found"
        login_sr = user_router.sub_routers.get("login")
        assert login_sr is not None, "login subrouter not found"
        login_ep = next((ep for ep in login_sr.endpoints if ep.name == "loginUser"), None)
        assert login_ep is not None, "loginUser endpoint not found"
        assert login_ep.response_schema_name is None, \
            f"loginUser response should be None (primitive string), got '{login_ep.response_schema_name}'"

    def test_login_user_empty_response_attrs(self, parsed_schema):
        """loginUser primitive response should have empty attributes list."""
        user_router = parsed_schema.routers["user"]
        login_sr = user_router.sub_routers["login"]
        login_ep = next(ep for ep in login_sr.endpoints if ep.name == "loginUser")
        if login_ep.response:
            assert len(login_ep.response.attributes) == 0, \
                f"Primitive response should have 0 attrs, got {len(login_ep.response.attributes)}"

    def test_logout_user_no_response(self, parsed_schema):
        """logoutUser (no content) should have no response at all."""
        user_router = parsed_schema.routers["user"]
        logout_sr = user_router.sub_routers["logout"]
        logout_ep = next(ep for ep in logout_sr.endpoints if ep.name == "logoutUser")
        assert logout_ep.response is None, "logoutUser should have no response object"
        assert logout_ep.response_schema_name is None, "logoutUser should have no response class"

    def test_entity_response_still_works(self, parsed_schema):
        """getPetById ($ref: Pet) should still have response class and Relation attrs."""
        pet_router = parsed_schema.routers["pet"]
        get_ep = next((ep for ep in pet_router.endpoints if ep.name == "getPetById"), None)
        assert get_ep is not None
        assert get_ep.response_schema_name is not None, "getPetById should have response class"
        relation_attrs = [a for a in get_ep.response.attributes if a.type == "Relation"]
        assert len(relation_attrs) > 0, "getPetById response should have Relation attributes"

