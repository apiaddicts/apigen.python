import json
from typing import Union, Dict, Any, List
import copy


from src.domain.parse_core.schemas.entity_schema import EntitySchema
from src.domain.parse_core.schemas.asyncapi_schema import (
    AsyncApiProjectSchema,
    AsyncProjectSchema,
)
from src.domain.parse_core.exceptions.parse_exceptions import (
    InvalidContentsException,
    InvalidModelDefinitionException,
)


class AsyncAPIParser:
    def __init__(self):
        self.definition = {}
        self.servers = {}
        self.channels = {}
        self.operations = {}
        self.entities: Dict[str, EntitySchema] = {}
        self.project: AsyncProjectSchema = None
        
    project_tag = "x-apigen-project"
    models_tag = "x-apigen-models"
    mapping_tag = "x-apigen-mapping"

    ref_tag = "$ref"


    def check_ref(self, definition_object):
        """Resolve $ref if present, handling None and empty dicts gracefully."""
        if not definition_object or not isinstance(definition_object, dict):
            return definition_object if definition_object is not None else {}

        _definition = (
            definition_object
            if self.ref_tag not in definition_object
            else self.get_ref(definition_object[self.ref_tag])
        )

        if not isinstance(_definition, dict) or self.ref_tag not in _definition:
            return _definition

        return self.get_ref(_definition[self.ref_tag])

    def _resolve_deep(self, obj: Any) -> Any:
        """Recursively resolve all $ref in a nested structure.

        When a $ref is resolved, the resulting dict is annotated with
        ``_original_ref`` so that downstream code can recover the original
        schema name (e.g. for oneOf variant detection or RPC reply DTO
        resolution).
        """
        if isinstance(obj, dict):
            if self.ref_tag in obj and len(obj) == 1:
                ref_path = obj[self.ref_tag]
                resolved = self.get_ref(ref_path)
                resolved = self._resolve_deep(resolved)
                if isinstance(resolved, dict):
                    resolved["_original_ref"] = ref_path
                return resolved
            return {k: self._resolve_deep(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._resolve_deep(item) for item in obj]
        return obj

    def load_definition(self, definition: Union[str, dict]):
        if isinstance(definition, dict):
            self.definition = definition
            return
        try:
            self.definition = json.loads(definition)
        except Exception as exception:
            raise InvalidContentsException(message=exception.msg)

    def get_ref(self, ref: str):
        _, first_path_step, *ref_path = ref.split("/")
        _ref = copy.deepcopy(self.definition[first_path_step])
        for path_step in ref_path:
            if path_step == "#":
                continue
            _ref = _ref[path_step]

        return _ref

    def get_project(self):
        """Extract x-apigen-project if present; build from info block otherwise."""
        info = self.definition.get("info", {})

        # Search root level first, then info block
        if self.project_tag in self.definition:
            self.project = AsyncProjectSchema(**self.definition[self.project_tag])
            return

        if self.project_tag in info:
            # Merge info.version and info.description as defaults
            project_data = {
                "version": info.get("version", "0.0.0"),
                "description": info.get("description", ""),
            }
            project_data.update(info[self.project_tag])
            self.project = AsyncProjectSchema(**project_data)
            return

        # Fallback: build project from AsyncAPI info block (specs without x-apigen)
        self.project = AsyncProjectSchema(
            name=info.get("title", "unnamed"),
            version=info.get("version", "0.0.0"),
            description=info.get("description", ""),
        )

    def get_entities(self):
        components = self.definition.get("components", {})
        if self.models_tag not in components:
            return
        apigen_models = components[self.models_tag]
        try:
            for model in apigen_models:
                if model in self.entities:
                    raise InvalidModelDefinitionException
                this_model = apigen_models[model]
                entity_input = {
                    "table": this_model["relational-persistence"]["table"],
                    **this_model,
                }
                self.entities[model] = EntitySchema(**entity_input)
        except Exception as _:
            raise InvalidModelDefinitionException(
                f"double definition for entity {model}"
            )

    def get_servers(self):
        definition_servers = self.definition.get("servers", {})
        for server_name in definition_servers:
            if self.ref_tag not in definition_servers[server_name]:
                self.servers[server_name] = definition_servers[server_name]
                continue

            self.servers[server_name] = self.get_ref(
                definition_servers[server_name][self.ref_tag]
            )

    def get_channels(self):
        definition_channels = self.definition.get("channels", {})
        for channel_name in definition_channels:
            channel = definition_channels[channel_name]
            if self.ref_tag in channel:
                channel = self.get_ref(channel[self.ref_tag])
            # Resolve $ref within parameters
            if "parameters" in channel:
                channel["parameters"] = self._resolve_parameters(channel["parameters"])
            self.channels[channel_name] = channel

    def _resolve_parameters(self, parameters: dict) -> dict:
        """Resolve $ref in channel parameters."""
        resolved = {}
        for param_name, param_value in parameters.items():
            if isinstance(param_value, dict) and self.ref_tag in param_value:
                resolved[param_name] = self.get_ref(param_value[self.ref_tag])
            else:
                resolved[param_name] = param_value
        return resolved

    def _merge_dict_no_overwrite(self, target: dict, source: dict) -> None:
        """Merge source keys into target without overwriting existing keys."""
        for key, value in source.items():
            if key not in target:
                target[key] = value

    def _merge_bindings(self, result: dict, trait_bindings: dict) -> None:
        """Deep-merge trait bindings into message (v3: no overwrite)."""
        if "bindings" not in result:
            result["bindings"] = {}
        for broker, config in trait_bindings.items():
            if broker not in result["bindings"]:
                result["bindings"][broker] = config
            else:
                self._merge_dict_no_overwrite(result["bindings"][broker], config)

    def _merge_headers(self, result: dict, trait_headers: dict) -> None:
        """Merge trait headers into message headers (v3: no overwrite)."""
        if "headers" not in result:
            result["headers"] = copy.deepcopy(trait_headers)
            return
        trait_props = trait_headers.get("properties", {})
        if "properties" not in result["headers"]:
            result["headers"]["properties"] = {}
        self._merge_dict_no_overwrite(result["headers"]["properties"], trait_props)

    def _apply_traits(self, message: dict) -> dict:
        """Apply message traits (v3: trait does NOT overwrite existing properties)."""
        traits = message.get("traits", [])
        if not traits:
            return message

        result = copy.deepcopy(message)
        del result["traits"]

        for trait_ref in traits:
            trait = self.check_ref(trait_ref)
            if not isinstance(trait, dict):
                continue

            if "bindings" in trait:
                self._merge_bindings(result, trait["bindings"])

            if "headers" in trait:
                self._merge_headers(result, trait["headers"])

            # Merge remaining top-level keys (v3: don't overwrite)
            skip_keys = ("bindings", "headers")
            for key, value in trait.items():
                if key not in skip_keys and key not in result:
                    result[key] = value

        return result

    def _get_operation_messages(self, messages_object):
        if not messages_object:
            return []
        messages = []
        for message in messages_object:
            _message = self.check_ref(message)
            # Apply traits if present
            if isinstance(_message, dict) and "traits" in _message:
                _message = self._apply_traits(_message)
            # ASYNC-021: Normalize 'schema' → 'payload' for compat
            # Some specs use 'schema' instead of 'payload' (pre-3.0 convention)
            if isinstance(_message, dict) and "schema" in _message and "payload" not in _message:
                _message["payload"] = _message.pop("schema")
            messages.append(_message)
        return messages

    def get_operations(self):
        definition_operations = self.definition.get("operations", {})

        for operation_name in definition_operations:
            operation_definition = definition_operations[operation_name]
            _action = operation_definition.get("action")

            _channel = operation_definition.get("channel")
            _channel = self.check_ref(_channel)

            _bindings = operation_definition.get("bindings", {})
            _bindings = self.check_ref(_bindings)

            _reply = operation_definition.get("reply", {})
            # Deep resolve reply (including nested channel $ref)
            if _reply:
                _reply = self._resolve_deep(_reply)

            _messages_obj = operation_definition.get("messages")
            # ASYNC-v3: Fallback to channel messages if operation omits them
            if not _messages_obj and _channel and isinstance(_channel, dict) and "messages" in _channel:
                _messages_obj = list(_channel["messages"].values())

            _messages = self._get_operation_messages(_messages_obj)

            _operation = {
                "action": _action,
                "channel": _channel,
                "bindings": _bindings,
                "reply": _reply,
                "messages": _messages,
            }
            self.operations[operation_name] = _operation

    # ── Schema composition (allOf / oneOf / anyOf) ───────────────

    def _resolve_payload_properties(self, schema: dict) -> dict:
        """Recursively resolve properties from a schema, handling allOf, oneOf, anyOf.
        
        Ported from OpenAPIParser._resolve_schema_properties() to support
        the same composition patterns in AsyncAPI payload schemas.
        """
        if not isinstance(schema, dict):
            return {}

        properties = {}

        if "allOf" in schema:
            for sub_schema in schema["allOf"]:
                resolved = self._resolve_payload_properties(sub_schema)
                properties.update(resolved)

        if "oneOf" in schema:
            for sub_schema in schema["oneOf"]:
                resolved = self._resolve_payload_properties(sub_schema)
                properties.update(resolved)

        if "anyOf" in schema:
            for sub_schema in schema["anyOf"]:
                resolved = self._resolve_payload_properties(sub_schema)
                properties.update(resolved)

        if self.ref_tag in schema:
            ref_schema = self.get_ref(schema[self.ref_tag])
            resolved = self._resolve_payload_properties(ref_schema)
            properties.update(resolved)

        if "properties" in schema:
            properties.update(schema["properties"])

        return properties

    def parse(self):
        assert len(self.definition) > 0, "asyncapi definition not loaded"
        self.get_project()
        self.get_entities()
        self.get_servers()
        self.get_channels()
        self.get_operations()

        components = self._resolve_deep(self.definition.get("components", {}))
        # ASYNC-021: Normalize 'schema' → 'payload' in components.messages
        for msg_data in components.get("messages", {}).values():
            if isinstance(msg_data, dict) and "schema" in msg_data and "payload" not in msg_data:
                msg_data["payload"] = msg_data.pop("schema")

        return AsyncApiProjectSchema(
            project=self.project,
            entities=self.entities,
            servers=self.servers,
            channels=self.channels,
            operations=self.operations,
            default_content_type=self.definition.get(
                "defaultContentType", "application/json"
            ),
            components=components,
        )
