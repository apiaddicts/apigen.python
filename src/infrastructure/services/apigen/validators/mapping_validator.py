from ..models.parameter_enum import ApigenProps

class MappingValidator:
    @staticmethod
    def validate(openapi_dict: dict, models: list[str]) -> list[str]:
        components = openapi_dict.get(ApigenProps.COMPONENTS, {})
        schemas = components.get(ApigenProps.SCHEMAS, {})
        for schema_name, schema_def in schemas.items():
            mapping = schema_def.get(ApigenProps.X_APIGEN_MAPPING)
            if not mapping:
                continue
            model = mapping.get(ApigenProps.MODEL)
            if not model:
                raise ValueError(
                    f"Schema '{schema_name}' has {ApigenProps.X_APIGEN_MAPPING} but no model defined."
                )
            if model not in models:
                raise ValueError(
                    f"Model '{model}' referenciado en el mapeo '{schema_name}' no está definido en {ApigenProps.X_APIGEN_MODELS}."
                )

    @staticmethod
    def validate_asyncapi(async_dict: dict, models: list[str], model_attrs: dict[str, list[str]]) -> None:
        """Validate x-apigen-mapping at schema and property level for AsyncAPI.

        Checks:
        1. Schema-level: model exists in x-apigen-models.
        2. Property-level: field references a valid attribute of the mapped model.
        """
        components = async_dict.get(ApigenProps.COMPONENTS, {})
        schemas = components.get(ApigenProps.SCHEMAS, {})
        for schema_name, schema_def in schemas.items():
            if not isinstance(schema_def, dict):
                continue
            mapping = schema_def.get(ApigenProps.X_APIGEN_MAPPING)
            if not mapping:
                continue
            model = mapping.get(ApigenProps.MODEL)
            if not model:
                raise ValueError(
                    f"Schema '{schema_name}' has {ApigenProps.X_APIGEN_MAPPING} but no model defined."
                )
            if model not in models:
                raise ValueError(
                    f"Model '{model}' referenciado en el mapeo '{schema_name}' no está definido en {ApigenProps.X_APIGEN_MODELS}."
                )
            # Validate property-level field mappings
            MappingValidator._validate_property_fields(
                schema_name, schema_def, model, model_attrs.get(model, [])
            )

    @staticmethod
    def _validate_property_fields(schema_name: str, schema_def: dict, model: str, attrs: list[str]) -> None:
        """Validate that property-level x-apigen-mapping.field values reference valid model attributes."""
        properties = schema_def.get("properties", {})
        for prop_name, prop_def in properties.items():
            if not isinstance(prop_def, dict):
                continue
            prop_mapping = prop_def.get(ApigenProps.X_APIGEN_MAPPING)
            if not prop_mapping:
                continue
            field = prop_mapping.get("field")
            if field and attrs and field not in attrs:
                raise ValueError(
                    f"Property '{prop_name}' in schema '{schema_name}' maps to field '{field}' "
                    f"which is not an attribute of model '{model}'. "
                    f"Valid attributes: {attrs}"
                )
