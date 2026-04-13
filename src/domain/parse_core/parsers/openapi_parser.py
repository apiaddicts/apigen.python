from itertools import zip_longest
import json
import yaml
from typing import Dict, Union, Any

from src.domain.parse_core.schemas.rest_schema import (
    RESTProjectSchema,
    OpenApiProjectSchema,
)
from src.domain.parse_core.schemas.entity_schema import EntitySchema
from src.domain.parse_core.schemas.router_schema import (
    EndpointSchema,
    RequestSchema,
    ResponseSchema,
    RouterSchema,
)
from src.domain.parse_core.exceptions.parse_exceptions import (
    InvalidContentsException,
    InvalidModelDefinitionException,
)
import copy


class OpenAPIParser:
    def __init__(self):
        self.project: OpenApiProjectSchema = None
        self.entities: Dict[str, EntitySchema] = {}
        self.routers: Dict[str, RouterSchema] = {}
        self.definition: dict = {}

    project_tag = "x-apigen-project"
    binding_tag = "x-apigen-binding"
    models_tag = "x-apigen-models"
    mapping_tag = "x-apigen-mapping"

    ref_tag = "$ref"

    def load_definition(
        self, spec_str: Union[str, bytes, bytearray] = None, spec_dict: dict = None
    ):
        if spec_dict:
            self.definition = spec_dict
            return

        try:
            self.definition = json.loads(spec_str)
        except json.JSONDecodeError:
            try:
                self.definition = yaml.safe_load(spec_str)
            except Exception as yaml_exception:
                raise InvalidContentsException(
                    message=f"Failed to parse content as JSON or YAML. Error: {str(yaml_exception)}"
                )
        except Exception as exception:
            raise InvalidContentsException(message=str(exception))

        if not isinstance(self.definition, dict):
            raise InvalidContentsException(
                message="Parsed content is not a valid dictionary (JSON object or YAML mapping)."
            )

    def get_ref(self, ref: str):
        _, first_path_step, *ref_path = ref.split("/")
        ref_temp = copy.deepcopy(self.definition[first_path_step])
        for path_step in ref_path:
            if path_step == "#":
                continue
            ref_temp = ref_temp[path_step]

        return ref_temp

    def explore_path(self, path):
        _, *path_steps = path.split("/")
        i = 0
        path_len = len(path_steps)
        depth = 0
        while i < path_len:
            path_resource = path_steps[i]
            path_param = None
            if i + 1 < path_len and path_steps[i+1].startswith("{") and path_steps[i+1].endswith("}"):
                path_param = path_steps[i+1]
                i += 2
            else:
                i += 1
            yield depth, (path_resource, path_param)
            depth += 1

    def get_project(self):
        assert self.project_tag in self.definition, "project definition not found"
        project_data = self.definition[self.project_tag]
        
        if "servers" in self.definition and len(self.definition["servers"]) > 0:
            server_url = self.definition["servers"][0].get("url", "")
            if server_url and server_url != "/":
                from urllib.parse import urlparse
                project_data["prefix"] = urlparse(server_url).path.rstrip("/")

        self.project = OpenApiProjectSchema(**project_data)

    @staticmethod
    def _to_snake_case(name: str) -> str:
        result = []
        for i, ch in enumerate(name):
            if ch.isupper() and i > 0:
                prev = name[i - 1]
                needs_sep = prev.islower() or prev.isdigit()
                if not needs_sep:
                    needs_sep = prev.isupper() and i + 1 < len(name) and name[i + 1].islower()
                if needs_sep:
                    result.append('_')
            result.append(ch.lower())
        return ''.join(result)

    def get_entities(self):
        components = self.definition.get("components", {})
        apigen_models = components.get(self.models_tag, {})
        if not apigen_models:
            print("INFO: No x-apigen-models found. Partial generation: only paths with binding+model will be generated.")
            return
        try:
            for model in apigen_models:
                if model in self.entities:
                    raise InvalidModelDefinitionException
                this_model = apigen_models[model]
                rp = this_model.get("relational-persistence", {})
                table = rp.get("table") if rp else None
                if not table:
                    table = self._to_snake_case(model)
                entity_input = {
                    "table": table,
                    **this_model,
                }
                self.entities[model] = EntitySchema(**entity_input)

            self._enrich_models_with_schemas()

        except Exception as _:
            raise InvalidModelDefinitionException(
                f"double definition for entity {model}"
            )

    def _enrich_models_with_schemas(self):
        """Enrich models with array metadata and relations from components.schemas."""
        components = self.definition.get("components", {})
        schemas = components.get("schemas", {})

        for schema_name, schema in schemas.items():
            self._process_single_schema(schema, schema_name)

    def _process_single_schema(self, schema: Dict[str, Any], schema_name: str):
        mapping = schema.get(self.mapping_tag, {})
        model_name = mapping.get("model", schema_name)

        if model_name not in self.entities:
            return

        props = schema.get("properties", {})
        if not props:
             resolved = self._resolve_schema_properties(schema)
             if resolved:
                 props = resolved

        target_model = self.entities[model_name]
        attr_index = {a.name: a for a in target_model.attributes}
        attr_index_snake = {self._to_snake_case(k): v for k, v in attr_index.items()}

        for prop_name, prop_data in props.items():
            attr = attr_index.get(prop_name)
            if not attr:
                field_mapping = prop_data.get(self.mapping_tag, {}).get("field", "")
                if field_mapping:
                    base_field = field_mapping.split(".")[0]
                    attr = attr_index.get(base_field)
            if not attr:
                attr = attr_index_snake.get(self._to_snake_case(prop_name))
            if attr:
                self._enrich_attribute(attr, prop_data)

    def _enrich_attribute(self, attr, prop_data: dict):
        """Mark attribute as exposed and apply type overrides from schema."""
        attr.is_exposed_in_schema = True
        api_type = prop_data.get("type")
        if api_type in ["array", "object"] and attr.type == "String" and not attr.is_array:
            attr.has_json_conversion = True

        if "$ref" in prop_data:
            attr.type = "Relation"
            if not attr.ref_model:
                attr.ref_model = self._ref_name(prop_data["$ref"])

        # OPENAPI-002: Capture readOnly/writeOnly from standard OpenAPI properties
        if prop_data.get("readOnly", False):
            attr.read_only = True
        if prop_data.get("writeOnly", False):
            attr.write_only = True

    def _ref_name(self, ref: str) -> str:
        """Resolve the model name from a JSON reference, checking x-apigen-mapping."""
        if not ref:
            return None
        return self._resolve_schema_model_name(ref)

    def _resolve_schema_model_name(self, ref: str) -> str:
        schema_name = ref.split("/")[-1]
        try:
            resolved = self.get_ref(ref)
        except (KeyError, TypeError):
            return schema_name
        if isinstance(resolved, dict):
            mapping = resolved.get(self.mapping_tag, {})
            if isinstance(mapping, dict) and mapping.get("model"):
                return mapping["model"]
        return schema_name

    def get_routers(self):
        paths: dict = self.definition.get("paths", None)
        assert paths is not None, "No paths in definition"
        for endpoint_path in paths:
            self.setup_routers(endpoint_path, paths[endpoint_path])

    def get_endpoints(self):
        paths: dict = self.definition.get("paths", None)
        assert paths is not None, "No paths in definition"

        for route in paths:
            self.setup_route_endpoints(route, paths[route])

    def setup_route_endpoints(self, path, path_definition):
        # PARTIAL-GEN: skip paths without binding
        if self.binding_tag not in path_definition:
            return

        router, path_param = self._find_router_for_path(path)
        if router is None or router.entity not in self.entities:
            return

        for method in path_definition:
            if method == self.binding_tag:
                continue
            endpoint = self._parse_endpoint_method(
                method, path_definition[method], router.entity, path_param
            )
            router.endpoints.append(endpoint)

    def _find_router_for_path(self, path):
        """Traverse routers to find the deepest router and its path param."""
        router = None
        path_param = None
        for _, (path_resource, _path_param) in self.explore_path(path):
            router_path = f"{path_resource}"
            path_param = _path_param
            if router is None:
                router = self.routers.get(router_path)
            else:
                router = router.get_subrouter(router_path) if router else None
        return router, path_param

    def _parse_endpoint_method(self, method, endpoint_definition, entity_name, path_param):
        """Parse a single HTTP method into an EndpointSchema."""
        parameter_list = None
        if "parameters" in endpoint_definition:
            parameter_list = self.parse_parameters(endpoint_definition["parameters"])

        response, response_schema_name, response_wrapper_field = (None, None, None)
        if "responses" in endpoint_definition:
            response, response_schema_name, response_wrapper_field = self.parse_response(
                endpoint_definition["responses"],
                entity_name,
                method,
                path_param is None,
            )

        request = None
        if "requestBody" in endpoint_definition:
            request = self.parse_request_body(
                endpoint_definition["requestBody"],
                entity_name,
                method,
            )

        endpoint_input = {
            "method": method,
            "name": endpoint_definition["operationId"],
            "mapping": "" if path_param is None else path_param,
            "parameters": parameter_list,
            "response": response,
            "response_schema_name": response_schema_name,
            "response_wrapper_field": response_wrapper_field,
            "responses": {
                int(k): v for k, v in endpoint_definition.get("responses", {}).items()
                if str(k).isdigit()
            },
            "request": request,
        }
        return EndpointSchema(**endpoint_input)

    def _get_router_entity(self, path_param, depth, max_depth, path_definition):
        binding = path_definition.get(self.binding_tag)
        if not binding:
            return None
        if path_param is not None and depth + 1 < max_depth:
            _path_param = path_param.replace("{", "").replace("}", "")
            if _path_param not in binding:
                return None
            return binding[_path_param].split(".")[0]
        return binding.get("model")

    def _get_or_create_router(self, router_path, router_entity, parent_router=None):
        if parent_router is None:
            if router_path not in self.routers:
                self.routers[router_path] = RouterSchema(
                    entity=router_entity, mapping=f"/{router_path}", endpoints=[]
                )
            return self.routers[router_path]
        
        assert parent_router is not None, "sub router found with no parent router"
        if parent_router.sub_routers is None:
            parent_router.sub_routers = {}
        
        if router_path not in parent_router.sub_routers:
            parent_router.sub_routers[router_path] = RouterSchema(
                entity=router_entity, mapping=f"/{router_path}", endpoints=[]
            )
        return parent_router.sub_routers[router_path]

    def setup_routers(self, path, path_definition):
        # PARTIAL-GEN: skip paths without binding
        if self.binding_tag not in path_definition:
            return

        parent_router = None
        max_depth = len(list(self.explore_path(path)))
        
        for depth, (path_resource, path_param) in self.explore_path(path):
            if depth >= 4:
                print(f"WARNING: Path {path} exceeds max depth of 4. Skipping.")
                return

            router_entity = self._get_router_entity(path_param, depth, max_depth, path_definition)
            if router_entity is None:
                return

            # PARTIAL-GEN: skip if model not in entities
            if router_entity not in self.entities:
                print(f"WARNING: Path {path} references model '{router_entity}' not defined in x-apigen-models. Skipping.")
                return

            router_path = f"{path_resource}"

            if depth == 0:
                parent_router = self._get_or_create_router(router_path, router_entity)
            else:
                parent_router = self._get_or_create_router(router_path, router_entity, parent_router)

    
    def _merge_properties(self, target, source):
        """Helper to merge properties dictionaries."""
        for key, value in source.items():
            target[key] = value
        return target

    def _resolve_schema_properties(self, schema):
        """
        Recursively resolve properties from the schema, handling allOf, oneOf, anyOf.
        Returns a dictionary of properties.
        """
        properties = {}

        if "allOf" in schema:
            for sub_schema in schema["allOf"]:
                resolved = self._resolve_schema_properties(sub_schema)
                self._merge_properties(properties, resolved)
        
        if "oneOf" in schema:
            for sub_schema in schema["oneOf"]:
                resolved = self._resolve_schema_properties(sub_schema)
                self._merge_properties(properties, resolved)

        if "anyOf" in schema:
            for sub_schema in schema["anyOf"]:
                resolved = self._resolve_schema_properties(sub_schema)
                self._merge_properties(properties, resolved)

        if self.ref_tag in schema:
             ref_schema = self.get_ref(schema[self.ref_tag])
             resolved = self._resolve_schema_properties(ref_schema)
             self._merge_properties(properties, resolved)

        if "properties" in schema:
            self._merge_properties(properties, schema["properties"])

        return properties

    def _map_request_attribute(self, attribute, properties, entity_attribute_map, _entity_name):
        """Resolve an attribute from properties to an entity attribute."""
        if attribute in entity_attribute_map:
            return entity_attribute_map[attribute]

        if self.mapping_tag not in properties[attribute]:
            return None
        entity_field = properties[attribute][self.mapping_tag]["field"]

        if entity_field in entity_attribute_map:
            return entity_attribute_map[entity_field]

        if "." in entity_field:
            root_field = entity_field.split(".")[0]
            if root_field in entity_attribute_map:
                return entity_attribute_map[root_field]

        return None

    def parse_request_body(self, request_body, entity_name, method):
        schema = self.get_schema_definition_by_model_and_method(entity_name, method)
        entity = self.entities[entity_name]
        entity_attribute_map = {
            attribute.name: attribute for attribute in entity.attributes
        }
        request_attributes = []
        assert schema is not None, "schema found with no method defined"
        
        properties = self._resolve_schema_properties(schema)
        
        for attribute in properties:
            entity_attribute = self._map_request_attribute(
                attribute, properties, entity_attribute_map, entity_name
            )
            if entity_attribute is None:
                continue

            attribute_input = {
                "name": attribute,
                "type": entity_attribute.type,
                "entity_field_name": entity_attribute.name,
                "validations": (
                    entity_attribute.column_properties.validations
                    if entity_attribute.column_properties is not None
                    else None
                ),
            }
            request_attributes.append(attribute_input)

        if not request_body.get("content"):
            return None
        mime_type, content_schema = request_body["content"].popitem()
        
        is_collection = False
        if content_schema and "schema" in content_schema:
            body_schema = content_schema["schema"]
            if body_schema.get("type") == "array" and "items" in body_schema:
                is_collection = True
        
        return RequestSchema(mime_type=mime_type, attributes=request_attributes, is_collection=is_collection)

    def compare_responses(self, responses):
        _response_code = None
        _response_code_str = None
        for response_code in responses:
            response_code_str = str(response_code)
            if not response_code_str.startswith("2"):
                continue
            if _response_code is None:
                _response_code = response_code
                _response_code_str = response_code_str

            if response_code_str < _response_code_str:
                _response_code = response_code
                _response_code_str = response_code_str
        assert _response_code is not None, ""
        return _response_code

    def _map_response_attribute(self, attribute, properties, entity_attribute_map, _route_entity):
        if attribute in entity_attribute_map:
            return entity_attribute_map[attribute]
        
        if self.mapping_tag not in properties[attribute]:
            return None
        entity_field = properties[attribute][self.mapping_tag]["field"]
        
        if entity_field in entity_attribute_map:
            return entity_attribute_map[entity_field]

        if "." in entity_field:
            root_field = entity_field.split(".")[0]
            if root_field in entity_attribute_map:
                return entity_attribute_map[root_field]
            
        return None

    def _resolve_response_type(self, response_attr_name, entity_attribute):
        """Resolve the correct type for a response attribute.
        
        When the response attribute name differs from the entity attribute name
        (e.g. 'categoryId' vs 'category') and the entity type is 'Relation',
        the attribute is a foreign key ID — use 'Long' instead of 'Relation'.
        
        When the entity attribute has items_ref_model set, it's a 1:N relation
        (e.g. visit, pet) and should be typed as 'Array' for List[X] generation.
        """
        if (entity_attribute.type == "Relation" 
                and response_attr_name != entity_attribute.name):
            return "Long"
        # 1:N relations (items_ref_model set) should be Array, not Relation
        if entity_attribute.type == "Relation" and entity_attribute.items_ref_model:
            return "Array"
        return entity_attribute.type

    def parse_response(self, responses, route_entity, method, is_collection):
        response_code = self.compare_responses(responses)
        response_to_map = responses[response_code]

        if self.ref_tag in response_to_map:
            response_to_map = self.get_ref(response_to_map[self.ref_tag])

        if "content" not in response_to_map:
            return None, None, None

        mime_type = next(iter(response_to_map["content"]))

        if method == "delete":
            return ResponseSchema(
                is_collection=is_collection, attributes=[], mime_type=mime_type
            ), None, None


        response_schema, response_schema_name, wrapper_field = self._extract_response_ref_schema(
            response_to_map
        )


        if response_schema is None:
            _primitive_types = {"string", "integer", "boolean", "number"}
            content = response_to_map.get("content", {})
            media = next(iter(content.values()), {}) if content else {}
            schema_type = media.get("schema", {}).get("type")
            if schema_type in _primitive_types:

                return ResponseSchema(
                    is_collection=is_collection, attributes=[], mime_type=mime_type
                ), None, None


        if response_schema is None:
            response_schema, response_schema_name = (
                self.get_schema_definition_by_model_and_method(route_entity, method)
            )

        assert response_schema is not None, f"response schema not found for method {method}"
        entity = self.entities[route_entity]
        entity_attribute_map = {
            attribute.name: attribute for attribute in entity.attributes
        }
        response_attributes = []

        properties = self._resolve_schema_properties(response_schema)
        for attribute in properties:
            entity_attribute = self._map_response_attribute(attribute, properties, entity_attribute_map, route_entity)
            if entity_attribute is None:
                continue

            attribute_input = {
                "name": attribute,
                "type": self._resolve_response_type(attribute, entity_attribute),
                "entity_field_name": entity_attribute.name,
                "ref_model": entity_attribute.ref_model or entity_attribute.items_ref_model,
                "validations": (
                    entity_attribute.column_properties.validations
                    if entity_attribute.column_properties is not None
                    else None
                ),
            }
            response_attributes.append(attribute_input)

        response_mapping_input = {
            "is_collection": is_collection,
            "attributes": response_attributes,
            "mime_type": mime_type,
        }
        return ResponseSchema(**response_mapping_input), response_schema_name, wrapper_field

    def _extract_response_ref_schema(self, response_to_map):
        """Extract schema dict, name, and wrapper field from response content $ref.

        Resolves the actual $ref in the response body (e.g. PetGet) instead
        of relying on method-based lookup (which would return PetPost for POST).
        Skips schemas without x-apigen-mapping to avoid creating ghost entities.
        Unwraps wrapper schemas like PetResponse{result, data: $ref PetGet}.
        """
        content = response_to_map.get("content", {})
        if not content:
            return None, None, None
        media = next(iter(content.values()), {})
        schema = media.get("schema", {})

        if self.ref_tag in schema:
            name = schema[self.ref_tag].rsplit("/", 1)[-1]
            resolved = self.get_ref(schema[self.ref_tag])
            if not resolved.get(self.mapping_tag):
                inner, inner_name, wrapper_field = self._unwrap_response_schema(resolved)
                if inner and inner.get(self.mapping_tag):
                    return inner, inner_name, wrapper_field
                return None, None, None
            return resolved, name, None

        if schema.get("type") == "array":
            items = schema.get("items", {})
            if self.ref_tag in items:
                name = items[self.ref_tag].rsplit("/", 1)[-1]
                resolved = self.get_ref(items[self.ref_tag])
                if not resolved.get(self.mapping_tag):
                    return None, None, None
                return resolved, name, None

        return None, None, None

    def _unwrap_response_schema(self, schema):
        """Unwrap wrapper schemas like {result, data: $ref ModelGet}."""
        props = schema.get("properties", {})
        for prop_name, prop_data in props.items():
            ref = prop_data.get(self.ref_tag)
            if not ref:
                continue
            inner = self.get_ref(ref)
            if isinstance(inner, dict) and inner.get(self.mapping_tag):
                inner_name = ref.rsplit("/", 1)[-1]
                return inner, inner_name, prop_name
        return None, None, None

    def get_schema_definition_by_model_and_method(self, model, method):
        """Return (schema_dict, schema_name) for the given model and method."""
        fallback_schema = None
        fallback_name = None
        for schema_name, schema in self.definition["components"]["schemas"].items():
            if self.mapping_tag in schema:
                mapping = schema[self.mapping_tag]
                if mapping["model"] == model:
                    if mapping.get("method", None) == method:
                        return schema, schema_name
                    if mapping.get("method", None) is None and fallback_schema is None:
                        fallback_schema = schema
                        fallback_name = schema_name
        return fallback_schema, fallback_name

    def parse_parameters(self, parameters_definitions):
        parameters = []
        for parameter_definition in parameters_definitions:
            if self.ref_tag in parameter_definition:
                parameter_definition = self.get_ref(parameter_definition[self.ref_tag])
            param_is_collection = parameter_definition["schema"]["type"] == "array"
            if param_is_collection:
                param_type = parameter_definition["schema"]["items"]["type"]
            else:
                param_type = parameter_definition["schema"]["type"]
            
            if param_type == "object":
                param_type = "string"

            default_value = parameter_definition["schema"].get("default", None)
            parameter_input = {
                "is_collection": param_is_collection,
                "name": parameter_definition["name"],
                "type": param_type,
                "required": parameter_definition.get("required", False),
                "in": parameter_definition["in"],
                "default": default_value,
                "validations": {},
            }
            parameters.append(parameter_input)

        return parameters

    def parse(self):
        assert len(self.definition) > 0, "openapi definition not loaded"
        self.get_project()
        self.get_entities()
        self._infer_relation_types()
        self._ensure_join_table_pks()
        self.get_routers()
        self.get_endpoints()
        return RESTProjectSchema(
            project=self.project.model_dump(by_alias=True),
            entities=self.entities,
            routers=self.routers,
        )

    def _normalize_foreign_columns(self):
        for entity in self.entities.values():
            for attr in entity.attributes:
                self._normalize_single_foreign_column(attr)

    def _normalize_single_foreign_column(self, attr):
        cp = attr.column_properties
        if not cp or not cp.foreign_column or '.' not in cp.foreign_column:
            return
        model_part, col_part = cp.foreign_column.split('.', 1)
        if attr.is_array:
            cp.foreign_column = self._resolve_fk_column_name(model_part, col_part)
        else:
            if not cp.column:
                cp.column = attr.name + '_id'
            cp.foreign_column = col_part

    def _resolve_fk_column_name(self, model_name: str, attr_name: str) -> str:
        target = self.entities.get(model_name)
        if not target:
            return attr_name
        attr = self._find_entity_attr(target, attr_name)
        if not attr:
            return attr_name
        if attr.type == "Relation" and not attr.is_array:
            return attr.column_properties.column if attr.column_properties and attr.column_properties.column else attr_name + '_id'
        if attr.column_properties and attr.column_properties.column:
            return attr.column_properties.column
        return attr_name

    @staticmethod
    def _find_entity_attr(entity, attr_name):
        for a in entity.attributes:
            if a.name == attr_name:
                return a
        return None

    def _infer_relation_types(self):
        self._normalize_foreign_columns()
        for entity in self.entities.values():
            for attr in entity.attributes:
                self._infer_single_relation_type(attr)

    @staticmethod
    def _infer_single_relation_type(attr):
        is_relation = attr.type == "Relation" or (attr.is_array and attr.items_ref_model)
        if not is_relation:
            return
        cp = attr.column_properties
        if not cp or cp.relation_type:
            return
        if attr.is_array:
            cp.relation_type = "ManyToMany" if cp.join_table else "OneToMany"
        else:
            cp.relation_type = "OneToOne" if (cp.foreign_column and not cp.column) else "ManyToOne"

    def _ensure_join_table_pks(self):
        """Detect join-table entities (no PK, 2+ FK relations) and add composite PK.

        SQLAlchemy requires every mapped table to have at least one primary key.
        Join tables have 2+ FK relations that together form a composite primary
        key.  Triggers when: no PK declared AND at least 2 non-array Relations.
        """
        for entity in self.entities.values():
            has_pk = any(
                a.column_properties and a.column_properties.primary_key
                for a in entity.attributes
            )
            if has_pk:
                continue
            fk_relations = [
                a for a in entity.attributes
                if a.type == "Relation" and not a.is_array
            ]
            if len(fk_relations) < 2:
                continue

            for attr in fk_relations:
                if attr.column_properties:
                    attr.column_properties.primary_key = True
