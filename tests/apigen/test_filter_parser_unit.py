import pytest
from src.domain.parse_core.parsers.openapi_parser import OpenAPIParser

def test_parser_extracts_filter_parameter():
    """
    Unit test for OpenAPIParser to verify it correctly extracts the filter 
    parameter from the spec into the internal EndpointSchema.
    This test does NOT depend on external templates or the full generator.
    """
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "x-apigen-project": {
            "name": "Test", 
            "version": "1.0.0", 
            "data-driver": "postgresql",
            "description": "Test description"
        },
        "paths": {
            "/pets": {
                "x-apigen-binding": {"model": "Pet"},
                "get": {
                    "operationId": "getPets",
                    "parameters": [
                        {
                            "name": "filter",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "OK"}}
                }
            }
        },
        "components": {
            "x-apigen-models": {
                "Pet": {
                    "relational-persistence": {"table": "pets"},
                    "attributes": [
                        {"name": "id", "type": "Long", "relational-persistence": {"column": "id", "primary-key": True}}
                    ]
                }
            }
        }
    }

    parser = OpenAPIParser()
    parser.load_definition(spec_dict=spec)
    parser.get_project()
    parser.get_entities()
    parser.get_routers()
    parser.get_endpoints()

    # The router path for /pets is "pets"
    assert "pets" in parser.routers
    router = parser.routers["pets"]
    
    # Find the GET endpoint
    endpoint = next(e for e in router.endpoints if e.method == "get")
    assert endpoint.name == "getPets"
    
    # Check that the parameters were parsed
    assert len(endpoint.parameters) == 1
    param = endpoint.parameters[0]
    
    # Verify that the parameter name filter is preserved in the internal schema
    # (The sanitization to 'filter' happens later in the Jinja templates)
    assert param.name == "filter"
    assert param.location == "query"
    assert param.type == "string"

def test_parser_without_filter_parameter():
    spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "x-apigen-project": {
            "name": "Test", 
            "version": "1.0.0", 
            "data-driver": "postgresql",
            "description": "Test description"
        },
        "paths": {
            "/pets": {
                "x-apigen-binding": {"model": "Pet"},
                "get": {
                    "operationId": "getPets",
                    "responses": {"200": {"description": "OK"}}
                }
            }
        },
        "components": {
            "x-apigen-models": {
                "Pet": {
                    "relational-persistence": {"table": "pets"},
                    "attributes": []
                }
            }
        }
    }

    parser = OpenAPIParser()
    parser.load_definition(spec_dict=spec)
    parser.get_project()
    parser.get_entities()
    parser.get_routers()
    parser.get_endpoints()

    router = parser.routers["pets"]
    endpoint = next(e for e in router.endpoints if e.method == "get")
    
    # Parameters should be empty or None depending on implementation
    if endpoint.parameters:
        filter_params = [p for p in endpoint.parameters if p.name == "filter"]
        assert len(filter_params) == 0
