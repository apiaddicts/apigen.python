from src.domain.parse_core.schemas.rest_schema import RESTProjectSchema
from src.domain.parse_core.schemas.router_schema import EndpointSchema

class OpenAPIStructure:
    TYPE_MAP: dict[str, str] = {
        "String": "string",
        "Integer": "integer",
        "Boolean": "boolean",
        "Float": "float",
        "Double": "double",
        "BigDecimal": "bigDecimal",
    }

    @staticmethod
    def _get_models(definition: RESTProjectSchema) -> dict:
        models = {}
        for entity_name, entity_schema in definition.entities.items():
            attrs = {}
            for attr in entity_schema.attributes:
                if attr.type == "Array":
                    value = f"Array<{attr.items_type}>"
                else:
                    value = attr.type
                attrs[attr.name] = value
            models[entity_name] = attrs
        return models

    @staticmethod
    def _get_router_request(endpoint: EndpointSchema):
        if not endpoint.request:
            return None
        body = {}
        for attr in endpoint.request.attributes:
            entity_type = attr.type
            body[attr.name] = OpenAPIStructure.TYPE_MAP.get(entity_type, "string")
        return body

    @staticmethod
    def _get_router_parameters(endpoint: EndpointSchema):
        if not endpoint.parameters:
            return None
        params_query = {}
        params_path = {}

        for param in endpoint.parameters:
            ptype = OpenAPIStructure.TYPE_MAP.get(param.type, "string")
            if param.location == "query":
                params_query[param.name] = ptype
            elif param.location == "path":
                params_path[param.name] = ptype

        params = {}
        if params_query:
            params["query"] = params_query
        if params_path:
            params["path"] = params_path
        return params if params else None

    @staticmethod
    def _get_response_data(endpoint: EndpointSchema):
        response_data = {}
        for attr in endpoint.response.attributes:
            entity_type = attr.type
            response_data[attr.name] = OpenAPIStructure.TYPE_MAP.get(entity_type, "string")

    @staticmethod
    def _get_routers(definition: RESTProjectSchema) -> dict:
        routers = {}
        for route_path, router in definition.routers.items():
            route_key = route_path.strip("/")
            routers[route_key] = {
                "model": router.entity
            }
            for endpoint in router.endpoints:
                method_key = endpoint.method.lower()
                routers[route_key][method_key] = {}

                body = OpenAPIStructure._get_router_request(endpoint)
                if body:
                    routers[route_key][method_key]["body"] = body
                params = OpenAPIStructure._get_router_parameters(endpoint)
                if params:
                    routers[route_key][method_key]["params"] = params

                response_data = OpenAPIStructure._get_response_data(endpoint)
                routers[route_key][method_key]["response"] = {
                    "result": {
                        "status": "boolean",
                        "http_code": "integer",
                        "errors": [
                            {
                                "code": "integer",
                                "message": "string"
                            }
                        ]
                    },
                    "data": response_data
                }
        return routers

    @staticmethod
    def load_structure(definition: RESTProjectSchema) -> dict:
        models = OpenAPIStructure._get_models(definition)

        routers = OpenAPIStructure._get_routers(definition)

        result = {
            "project": {
                "name": definition.project.name,
                "version": definition.project.version,
                "description": definition.project.description,
                "metadata": {
                    "data_driver": definition.project.data_driver
                }
            },
            "type": "openapi",
            "routes": routers,
            "queries": None,
            "channels": None,
            "models": models
        }
        return result
