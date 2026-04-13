import base64
from typing import Callable
from fastapi import Depends

from src.domain.parse_core.schemas.graphql_schema import (
    DirectiveSchema,
    GraphqlProjectDefinition,
    GraphqlProjectSchema,
    GraphqlSchemaSchema,
    InputSchema,
    InterfaceSchema,
    MutationSchema,
    QuerySchema,
    TypeSchema,
)
from src.domain.parse_core.exceptions.parse_exceptions import InvalidContentsException
from src.infrastructure.services.validators.graphql_validator_service import (
    GraphQLValidatorService,
)


def handle_errors(func: Callable):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as _:
            raise InvalidContentsException

    return wrapper


class GraphqlParser:

    project_tag = "XApiGenProject"

    operation_type_tag = "XApiGenOperationType"

    value_tag = "XApiGenValue"
    operation_tag = "XApiGenOperation"
    entity_tag = "XApiGenEntity"
    entity_field_tag = "XApiGenEntityField"
    entity_relation_tag = "XApiGenEntityRelation"
    map_arg_to_entity_tag = "XApiGenMapArgToEntity"

    apigen_enums = {operation_type_tag}
    apigen_directives_tags = {
        project_tag,
        value_tag,
        operation_tag,
        entity_tag,
        entity_field_tag,
        entity_relation_tag,
        map_arg_to_entity_tag,
    }
    apigen_types = {project_tag}

    graphql_query_type = "Query"
    graphql_mutation_type = "Mutation"
    graphql_subscription_type = "Subscription"
    reserved_graphql_types = {
        graphql_query_type,
        graphql_mutation_type,
        graphql_subscription_type,
    }

    built_in_directives = {
        "include",
        "skip",
        "deprecated",
        "specifiedBy",
    }

    framework_directives = built_in_directives.union(apigen_directives_tags)

    def __init__(self, graphql_validator_service: GraphQLValidatorService = Depends()):
        self.graphql_validator_service = graphql_validator_service
        self.schema_definition = None
        self.project: GraphqlProjectDefinition = None
        self.schema: GraphqlSchemaSchema = None
        self.schema_defined_directives = set()
        self.schema_defined_enums = set()
        self.schema_defined_interfaces = set()


    def load_definition(self, definition_str: str):
        self.schema_definition = (
            self.graphql_validator_service.build_schema_from_string(definition_str)
        )

    @staticmethod
    def get_directive_argument_value(
        argument_name, directive_name=None, graphql_element=None
    ):
        assert hasattr(graphql_element, "ast_node"), "error while reading directive arguments node"
        assert directive_name is not None and graphql_element is not None, "error while reading directive arguments values"

        applied_directives = graphql_element.ast_node.directives
        if len(applied_directives) == 0:
            return None

        found_directive = False
        for directive in applied_directives:
            if directive.name.value == directive_name:
                found_directive = True
                break

        if not found_directive:
            return None

        for argument in directive.arguments:
            if argument.name.value == argument_name:
                return argument.value.value

    @staticmethod
    def get_applied_directive_arguments(directive_node=None):
        assert directive_node is not None, "error while reading directive node"
        assert hasattr(directive_node, "arguments"), "error while reading directive arguments"

        return {
            argument.name.value: argument.value.value
            for argument in directive_node.arguments
        }

    def get_project(self):
        assert self.schema_definition is not None, "error while reading schema definition"
        assert self.project_tag in self.schema_definition.type_map, "error while reading project definition"
        project_type_definition_fields = self.schema_definition.type_map[
            self.project_tag
        ].fields
        project_input = {}
        for field in project_type_definition_fields:
            field_value = self.get_directive_argument_value(
                "value",
                graphql_element=project_type_definition_fields[field],
                directive_name=self.value_tag,
            )
            project_input[field] = field_value
        self.project = GraphqlProjectDefinition(**project_input)

    def get_node_directives(self, node_definition):
        applied_directives = {}
        if not hasattr(node_definition, "ast_node"):
            return applied_directives
        for directive in node_definition.ast_node.directives:
            directive_name = directive.name.value
            if directive_name not in self.framework_directives:
                assert directive_name in self.schema_defined_directives, "node found with directive that is not defined"
            applied_directives[directive_name] = self.get_applied_directive_arguments(
                directive
            )
        return applied_directives

    def get_field_type(self, node_definition):
        data_type = None
        type_node = node_definition.type
        non_null_field = False
        enum_field = False

        while type_node is not None:
            non_null_node = self.graphql_validator_service.is_not_null(type_node)
            is_type = (
                hasattr(type_node, "name")
                or self.graphql_validator_service.is_enum(type_node)
                or self.graphql_validator_service.is_type(type_node)
                or self.graphql_validator_service.is_input(type_node)
            )
            if non_null_node:
                if "is_array" in locals():
                    not_null_elements = True
                else:
                    non_null_field = True
            elif "is_array" not in locals():
                is_array = self.graphql_validator_service.is_list(type_node)
            if is_type:
                enum_field = self.graphql_validator_service.is_enum(type_node)
                data_type = type_node.name

            type_node = type_node.of_type if hasattr(type_node, "of_type") else None

        type_output = {
            "type": data_type,
            "is_enum": enum_field,
            "not_null": non_null_field,
            "is_array": is_array if "is_array" in locals() else False,
            "not_null_elements": (
                not_null_elements if "not_null_elements" in locals() else False
            ),
        }
        return type_output

    # @staticmethod
    def get_node_fields(self, node_definition, field_type="fields"):
        fields = {}
        assert hasattr(node_definition, field_type), "node found with no field type defined"

        field_dict = getattr(node_definition, field_type)
        for attrubute_name in field_dict:
            field_node_definition = field_dict[attrubute_name]
            fields[attrubute_name] = {
                **self.get_field_type(field_node_definition),
                "directives": self.get_node_directives(field_node_definition),
            }
        return fields

    def get_node_interfaces(self, node_definition):
        interfaces = set()
        if not hasattr(node_definition, "interfaces"):
            return interfaces
        for interface in node_definition.interfaces:
            assert interface.name in self.schema_defined_interfaces, "node found implementing not defined interface"
            interfaces.add(interface.name)
        return list(interfaces)

    def get_schema_directives(self):
        directives = {}
        get_location_name = lambda location: location.name
        for directive_definition in self.schema_definition.directives:
            directive_name = directive_definition.name
            if directive_name in self.framework_directives:
                continue

            locations = {
                get_location_name(location)
                for location in directive_definition.locations
            }

            directives[directive_name] = DirectiveSchema(
                arguments=self.get_node_fields(directive_definition, "args"),
                locations=list(locations),
            )
        self.schema_defined_directives = set(directives.keys())
        return directives

    def get_interfaces(self):
        interfaces = {}
        for type_definition_name in self.schema_definition.type_map:
            if not self.graphql_validator_service.is_interface(
                self.schema_definition.type_map[type_definition_name]
            ):
                continue

            interface_definition = self.schema_definition.type_map[type_definition_name]
            interface_input = {
                "fields": self.get_node_fields(
                    interface_definition,
                    field_type="fields",
                ),
                "directives": self.get_node_directives(interface_definition),
            }
            interfaces[type_definition_name] = InterfaceSchema(**interface_input)
            self.schema_defined_interfaces.add(type_definition_name)

        return interfaces

    def get_types(self):
        types = {}
        for type_definition_name in self.schema_definition.type_map:
            if (
                not self.graphql_validator_service.is_type(
                    self.schema_definition.type_map[type_definition_name]
                )
                or type_definition_name in self.apigen_types
                or type_definition_name.startswith("__")
                or type_definition_name in self.reserved_graphql_types
            ):
                continue

            type_definition = self.schema_definition.type_map[type_definition_name]

            type_input = {
                "interfaces": self.get_node_interfaces(type_definition),
                "fields": self.get_node_fields(type_definition),
                "directives": self.get_node_directives(type_definition),
            }
            types[type_definition_name] = TypeSchema(**type_input)
        return types

    def get_queries(self):
        queries = {}
        query_object_definition = self.schema_definition.query_type
        for query_name in query_object_definition.fields:
            query_field_definition = query_object_definition.fields[query_name]

            query_input = {
                **self.get_field_type(query_field_definition),
                "arguments": self.get_node_fields(
                    query_field_definition, field_type="args"
                ),
                "directives": self.get_node_directives(query_field_definition),
            }
            queries[query_name] = QuerySchema(**query_input)
        return queries

    def get_inputs(self):
        inputs = {}
        for type_definition_name in self.schema_definition.type_map:
            if (
                not self.graphql_validator_service.is_input(
                    self.schema_definition.type_map[type_definition_name]
                )
                or type_definition_name.startswith("__")
                or type_definition_name in self.reserved_graphql_types
            ):
                continue
            input_definition = self.schema_definition.type_map[type_definition_name]
            input_input = {
                "fields": self.get_node_fields(input_definition),
                "directives": self.get_node_directives(input_definition),
            }
            inputs[type_definition_name] = InputSchema(**input_input)
        return inputs

    def parse_enum_definition(self, definition):
        enum_definition = {}
        for value in definition.values:
            enum_definition[value] = {
                "directives": self.get_node_directives(definition.values[value])
            }
        return enum_definition

    def get_enums(self):
        enums = {}
        for type_definition_name in self.schema_definition.type_map:
            if (
                not self.graphql_validator_service.is_enum(
                    self.schema_definition.type_map[type_definition_name]
                )
                or type_definition_name.startswith("__")
                or type_definition_name in self.apigen_enums
            ):
                continue

            enum_definition = self.schema_definition.type_map[type_definition_name]
            enums[type_definition_name] = self.parse_enum_definition(enum_definition)

        self.schema_defined_enums = set(enums.keys())
        return enums

    def get_mutations(self):
        mutations = {}
        mutations_definition = self.schema_definition.type_map[
            self.graphql_mutation_type
        ]
        for mutation_name in mutations_definition.fields:
            mutation_definition = mutations_definition.fields[mutation_name]

            mutation_input = {
                **self.get_field_type(mutation_definition),
                "arguments": self.get_node_fields(
                    mutation_definition, field_type="args"
                ),
                "directives": self.get_node_directives(mutation_definition),
            }
            mutations[mutation_name] = MutationSchema(**mutation_input)
        return mutations

    def get_schema(self):
        schema_input = {
            "directives": self.get_schema_directives(),
            "enums": self.get_enums(),
            "interfaces": self.get_interfaces(),
            "types": self.get_types(),
            "inputs": self.get_inputs(),
            "queries": self.get_queries(),
            "mutations": self.get_mutations(),
        }
        self.schema = GraphqlSchemaSchema(**schema_input)

    @handle_errors
    def parse(self):
        assert self.schema_definition is not None, "schema not loaded"
        self.get_project()
        self.get_schema()
        return GraphqlProjectSchema(project=self.project, graphql_schema=self.schema)
