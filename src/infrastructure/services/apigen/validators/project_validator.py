from ..models.project_contract import ApigenProject
from ..models.parameter_enum import ApigenProps
from typing import Optional, Dict, Any

from graphql import parse
from graphql.language import (
    DocumentNode,
    ObjectTypeDefinitionNode,
    FieldDefinitionNode,
    DirectiveNode,
    StringValueNode,
    NamedTypeNode,
)

class ProjectValidator:
    @staticmethod
    def validate(open_api: dict):
        data = open_api.get(ApigenProps.X_APIGEN_PROJECT)
        if not data:
            raise ValueError(f"Falta el nodo {ApigenProps.X_APIGEN_PROJECT} en la definición OpenAPI.")
        try:
            ApigenProject(**data)
        except Exception as e:
            if hasattr(e, "errors"):
                error_messages = []
                for err in e.errors():
                    loc_parts = [str(l) for l in err["loc"]]
                    loc = ".".join(loc_parts)
                    msg = err["msg"]
                    
                    if "data-driver" in loc_parts or "data_driver" in loc_parts:
                         msg = "unidentified driver, please use mysql, postgresql or mssql"
                    
                    error_messages.append(f"{loc}: {msg}")
                
                raise ValueError(
                    f"Errores de validación en x-apigen-project: {', '.join(error_messages)}"
                )
            raise ValueError(f"Error en la configuración del proyecto: {str(e)}")

    @staticmethod
    def validate_graphql(graphql: dict):
        data = ProjectValidator.sdl_x_apigen_project_to_dict(graphql)
        if not data:
            raise ValueError("Falta el nodo XApiGenProject en la definición GraphQL.")
        try:
            ApigenProject(**data)
        except Exception as e:
            if hasattr(e, "errors"):
                missing_fields = [
                    err["loc"] for err in e.errors() if err["type"] == "missing"
                ]
                missing_names = [".".join(loc) for loc in missing_fields]
                raise ValueError(
                    f"Faltan los siguientes campos obligatorios: {', '.join(missing_names)}"
                )
            raise ValueError(f"Error en la configuración del proyecto: {str(e)}")

    @staticmethod
    def _unwrap_named_type(t):
        while hasattr(t, "type"):
            t = t.type
        return t

    @staticmethod
    def _get_field_directive(field: FieldDefinitionNode, name: str) -> Optional[DirectiveNode]:
        for d in field.directives or []:
            if d.name.value == name:
                return d
        return None

    @staticmethod
    def _get_directive_string_arg(directive: DirectiveNode, arg_name: str) -> Optional[str]:
        arg = next((a for a in directive.arguments or [] if a.name.value == arg_name), None)
        if not arg or not isinstance(arg.value, StringValueNode):
            return None
        return arg.value.value

    @staticmethod
    def _find_x_apigen_project(doc: DocumentNode) -> Optional[ObjectTypeDefinitionNode]:
        for defn in doc.definitions:
            if isinstance(defn, ObjectTypeDefinitionNode) and defn.name.value == "XApiGenProject":
                return defn
        return None

    @staticmethod
    def _required_fields(required_fields: list[str], fields: Dict[str, FieldDefinitionNode]) -> Dict[str, str]:
        out = {}
        for fname in required_fields:
            f = fields.get(fname)
            if not f:
                raise ValueError(f"[XApiGenProject] Falta campo obligatorio `{fname}`.")
            named = ProjectValidator._unwrap_named_type(f.type)
            if not (isinstance(named, NamedTypeNode) and named.name.value == "String"):
                raise ValueError(f"[XApiGenProject.{fname}] El tipo debe ser `String`.")
            d = ProjectValidator._get_field_directive(f, "XApiGenValue")
            if not d:
                raise ValueError(f"[XApiGenProject.{fname}] Falta directiva `@XApiGenValue`.")
            val = ProjectValidator._get_directive_string_arg(d, "value")
            if val is None or val == "":
                raise ValueError(f"[XApiGenProject.{fname}] `@XApiGenValue(value: ...)` debe ser string literal no vacío.")
            out[fname] = val
        return out

    @staticmethod
    def sdl_x_apigen_project_to_dict(sdl: str) -> Dict[str, Any]:
        doc: DocumentNode = parse(sdl)
        x_apigen_project_type = ProjectValidator._find_x_apigen_project(doc)

        if not x_apigen_project_type:
            raise ValueError("No se encontró `type XApiGenProject` en el SDL.")
        fields: Dict[str, FieldDefinitionNode] = {f.name.value: f for f in (x_apigen_project_type.fields or [])}
        required_fields = ["name", "description", "version", "data_driver", "app_prefix"]
        out: Dict[str, Any] = ProjectValidator._required_fields(required_fields, fields)
        return out
