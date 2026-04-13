"""
Esquema de referencia completo para parámetros x-apigen-*
Este módulo proporciona la documentación completa y ejemplos de todos los parámetros x-apigen
"""
PATIENT_ID_FIELD = "Patient.id"

example = PATIENT_ID_FIELD
second_example = PATIENT_ID_FIELD
third_example = PATIENT_ID_FIELD

APPLICATION_JSON: str = "application/json"

def get_complete_schema():
    """
    Retorna la estructura completa de todos los parámetros x-apigen con ejemplos y descripciones
    """
    return {
        "x-apigen-project": {
            "description": "Configuración principal del proyecto a generar. Debe colocarse en el nivel raíz del documento OpenAPI.",
            "location": "Nivel raíz del OpenAPI (mismo nivel que 'info', 'paths', etc.)",
            "required": True,
            "structure": {
                "name": {
                    "type": "string",
                    "required": True,
                    "description": "Nombre del proyecto",
                    "example": "Hospital Management API"
                },
                "description": {
                    "type": "string",
                    "required": False,
                    "description": "Descripción del proyecto",
                    "example": "API para gestión hospitalaria"
                },
                "version": {
                    "type": "string",
                    "required": True,
                    "description": "Versión del proyecto",
                    "example": "1.0.0"
                },
                "data-driver": {
                    "type": "string",
                    "required": True,
                    "description": "Driver de base de datos a utilizar",
                    "allowed_values": ["mysql", "oracle", "postgresql", "s3", "mssql"],
                    "example": "postgresql"
                },
                "python-properties": {
                    "type": "object",
                    "required": True,
                    "description": "Propiedades específicas de Python",
                    "structure": {
                        "artifact-id": {
                            "type": "string",
                            "required": True,
                            "description": "Identificador del artefacto/módulo Python",
                            "example": "hospital"
                        }
                    }
                }
            },
            "complete_example": {
                "name": "Hospital Management API",
                "description": "API para gestión de pacientes y habitaciones hospitalarias",
                "version": "1.0.0",
                "data-driver": "postgresql",
                "python-properties": {
                    "artifact-id": "hospital"
                }
            }
        },
        "x-apigen-models": {
            "description": "Define los modelos de base de datos y sus atributos. Se coloca dentro de 'components'.",
            "location": "components.x-apigen-models",
            "required": True,
            "structure": {
                "ModelName": {
                    "description": "Nombre del modelo (ej: Patient, Room, User)",
                    "relational-persistence": {
                        "type": "object",
                        "required": True,
                        "description": "Configuración de persistencia en base de datos",
                        "structure": {
                            "table": {
                                "type": "string",
                                "required": True,
                                "description": "Nombre de la tabla en base de datos",
                                "example": "patients"
                            }
                        }
                    },
                    "attributes": {
                        "type": "array",
                        "required": True,
                        "description": "Lista de atributos del modelo",
                        "item_structure": {
                            "name": {
                                "type": "string",
                                "required": True,
                                "description": "Nombre del atributo",
                                "example": "id"
                            },
                            "type": {
                                "type": "string",
                                "required": True,
                                "description": "Tipo de dato",
                                "allowed_values": ["String", "Integer", "Long", "Boolean", "LocalDate", "LocalDateTime", "Array", "Relation"],
                                "example": "String"
                            },
                            "relational-persistence": {
                                "type": "object",
                                "required": False,
                                "description": "Configuración de columna en BD",
                                "structure": {
                                    "column": {
                                        "type": "string",
                                        "description": "Nombre de columna en BD (opcional si coincide con 'name')",
                                        "example": "user_id"
                                    },
                                    "primary-key": {
                                        "type": "boolean",
                                        "description": "Indica si es clave primaria",
                                        "example": True
                                    },
                                    "autogenerated": {
                                        "type": "boolean",
                                        "description": "Indica si se autogenera el valor",
                                        "example": True
                                    },
                                    "foreign-column": {
                                        "type": "string",
                                        "description": "Columna foránea (formato: ModelName.column)",
                                        "example": example
                                    }
                                }
                            },
                            "validations": {
                                "type": "array",
                                "required": False,
                                "description": "Validaciones del campo",
                                "example": [{"type": "NotEmpty"}, {"type": "NotNull"}]
                            },
                            "items-type": {
                                "type": "string",
                                "required": False,
                                "description": "Tipo de elementos (cuando type='Array')",
                                "example": "Stay"
                            }
                        }
                    }
                }
            },
            "complete_example": {
                "Patient": {
                    "relational-persistence": {
                        "table": "patients"
                    },
                    "attributes": [
                        {
                            "name": "id",
                            "type": "String",
                            "relational-persistence": {
                                "primary-key": True,
                                "autogenerated": True
                            }
                        },
                        {
                            "name": "name",
                            "type": "String",
                            "validations": [{"type": "NotEmpty"}]
                        },
                        {
                            "name": "email",
                            "type": "String"
                        }
                    ]
                },
                "Room": {
                    "relational-persistence": {
                        "table": "rooms"
                    },
                    "attributes": [
                        {
                            "name": "id",
                            "type": "String",
                            "relational-persistence": {
                                "primary-key": True,
                                "autogenerated": True
                            }
                        },
                        {
                            "name": "code",
                            "type": "String",
                            "validations": [{"type": "NotEmpty"}]
                        },
                        {
                            "name": "active",
                            "type": "Boolean"
                        }
                    ]
                }
            }
        },
        "x-apigen-binding": {
            "description": "Vincula un path de operación con un modelo de base de datos. Se coloca a nivel de path o de operación.",
            "location": "paths.<path>.x-apigen-binding o paths.<path>.<method>.x-apigen-binding",
            "required": True,
            "required_for": "Cada path que interactúe con base de datos",
            "structure": {
                "model": {
                    "type": "string",
                    "required": True,
                    "description": "Nombre del modelo al que se vincula (debe existir en x-apigen-models)",
                    "example": "Patient"
                },
                "paramName": {
                    "type": "string",
                    "required": False,
                    "description": "Mapeo de parámetro de path a atributo del modelo. Solo requerido si el path tiene 2+ parámetros.",
                    "format": "ModelName.attributeName",
                    "example": second_example,
                    "note": "La clave es el nombre del parámetro en el path (ej: 'userId' de '/users/{userId}')"
                }
            },
            "complete_examples": [
                {
                    "description": "Path sin parámetros",
                    "path": "/patients",
                    "binding": {
                        "model": "Patient"
                    }
                },
                {
                    "description": "Path con 1 parámetro (no requiere mapeo explícito)",
                    "path": "/patients/{id}",
                    "binding": {
                        "model": "Patient"
                    }
                },
                {
                    "description": "Path con 2+ parámetros (requiere mapeo)",
                    "path": "/patients/{patientId}/stays/{stayId}",
                    "binding": {
                        "model": "Stay",
                        "patientId": third_example,
                        "stayId": "Stay.id"
                    }
                }
            ]
        },
        "x-apigen-mapping": {
            "description": "Mapea un schema de request/response a un modelo de base de datos. Se usa tanto en OpenAPI como en AsyncAPI. "
                           "A nivel de schema: vincula el schema completo con un modelo. "
                           "A nivel de propiedad: vincula cada campo del DTO con un atributo del modelo (field), "
                           "asegurando el mapeo aunque los nombres difieran.",
            "location": "components.schemas.<SchemaName>.x-apigen-mapping (schema-level) | "
                        "components.schemas.<SchemaName>.properties.<prop>.x-apigen-mapping (property-level)",
            "required": True,
            "required_for": "Cada schema que represente un modelo de BD (schema-level). "
                            "Cada propiedad cuyo nombre difiera del atributo del modelo (property-level).",
            "structure": {
                "model": {
                    "type": "string",
                    "required": True,
                    "description": "Nombre del modelo al que se mapea (debe existir en x-apigen-models). Solo a nivel de schema.",
                    "example": "Patient"
                },
                "method": {
                    "type": "string",
                    "required": False,
                    "description": "Método HTTP asociado al schema (solo OpenAPI)",
                    "allowed_values": ["get", "post", "put", "delete"],
                    "example": "get"
                },
                "field": {
                    "type": "string",
                    "required": False,
                    "description": "Mapeo de campo del schema a atributo del modelo. "
                                   "Se coloca en cada propiedad individual para vincularla con el atributo de BD correspondiente. "
                                   "Funciona igual en OpenAPI y AsyncAPI.",
                    "example": "entryDate"
                }
            },
            "complete_examples": [
                {
                    "description": "Schema de respuesta GET (OpenAPI)",
                    "schema_name": "Patient",
                    "mapping": {
                        "model": "Patient",
                        "method": "get"
                    }
                },
                {
                    "description": "Schema de request POST (OpenAPI)",
                    "schema_name": "CreatePatientRequest",
                    "mapping": {
                        "model": "Patient",
                        "method": "post"
                    }
                },
                {
                    "description": "Mapeo de campo individual con nombre diferente (OpenAPI/AsyncAPI)",
                    "schema_name": "StayResponse",
                    "property": "entry_date",
                    "property_mapping": {
                        "field": "entryDate"
                    },
                    "note": "Se coloca en la propiedad del schema, no en el nivel raíz"
                },
                {
                    "description": "Payload AsyncAPI con mapeo por propiedad",
                    "schema_name": "lightMeasuredPayload",
                    "schema_level_mapping": {
                        "model": "LightMeasurement"
                    },
                    "properties_example": {
                        "lumens": {
                            "type": "integer",
                            "x-apigen-mapping": {"field": "lumens"}
                        },
                        "sentAt": {
                            "type": "string",
                            "format": "date-time",
                            "x-apigen-mapping": {"field": "sent_at"}
                        }
                    },
                    "note": "Cada propiedad tiene x-apigen-mapping.field apuntando al atributo del modelo en x-apigen-models. "
                            "Esto asegura el vinculo aunque los nombres del DTO y la BD difieran."
                }
            ]
        }
    }


def get_minimal_working_example():
    """
    Retorna un ejemplo mínimo funcional de OpenAPI con todos los parámetros x-apigen
    """
    return {
        "openapi": "3.0.1",
        "info": {
            "title": "Example API",
            "version": "1.0.0"
        },
        "x-apigen-project": {
            "name": "Example Project",
            "version": "1.0.0",
            "data-driver": "postgresql",
            "python-properties": {
                "artifact-id": "example"
            }
        },
        "paths": {
            "/users": {
                "x-apigen-binding": {
                    "model": "User"
                },
                "get": {
                    "summary": "List users",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                APPLICATION_JSON: {
                                    "schema": {
                                        "type": "array",
                                        "items": {
                                            "$ref": "#/components/schemas/User"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": "Create user",
                    "requestBody": {
                        "content": {
                            APPLICATION_JSON: {
                                "schema": {
                                    "$ref": "#/components/schemas/CreateUser"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created"
                        }
                    }
                }
            },
            "/users/{id}": {
                "x-apigen-binding": {
                    "model": "User"
                },
                "get": {
                    "summary": "Get user by ID",
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                APPLICATION_JSON: {
                                    "schema": {
                                        "$ref": "#/components/schemas/User"
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "x-apigen-mapping": {
                        "model": "User",
                        "method": "get"
                    },
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "email": {
                            "type": "string"
                        }
                    }
                },
                "CreateUser": {
                    "x-apigen-mapping": {
                        "model": "User",
                        "method": "post"
                    },
                    "type": "object",
                    "required": ["name", "email"],
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "email": {
                            "type": "string"
                        }
                    }
                }
            },
            "x-apigen-models": {
                "User": {
                    "relational-persistence": {
                        "table": "users"
                    },
                    "attributes": [
                        {
                            "name": "id",
                            "type": "String",
                            "relational-persistence": {
                                "primary-key": True,
                                "autogenerated": True
                            }
                        },
                        {
                            "name": "name",
                            "type": "String",
                            "validations": [
                                {
                                    "type": "NotEmpty"
                                }
                            ]
                        },
                        {
                            "name": "email",
                            "type": "String",
                            "validations": [
                                {
                                    "type": "NotEmpty"
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }


def get_validation_error_response(validation_results: dict):
    """
    Genera una respuesta de error enriquecida con la documentación completa
    """
    return {
        "error": "x-apigen validation failed",
        "validation_results": validation_results,
        "documentation": {
            "message": "Su archivo OpenAPI no cumple con los requisitos de parámetros x-apigen. A continuación se muestra la estructura completa requerida:",
            "complete_schema": get_complete_schema(),
            "minimal_working_example": get_minimal_working_example(),
            "help": {
                "description": "Los parámetros x-apigen son extensiones personalizadas de OpenAPI que permiten vincular su especificación con modelos de base de datos.",
                "required_parameters": [
                    "x-apigen-project (nivel raíz)",
                    "x-apigen-models (en components)",
                    "x-apigen-binding (en cada path operacional)",
                    "x-apigen-mapping (en cada schema de components)"
                ],
                "validation_order": [
                    "1. Se valida x-apigen-project",
                    "2. Se valida x-apigen-models",
                    "3. Se valida x-apigen-binding en paths",
                    "4. Se valida x-apigen-mapping en schemas"
                ]
            }
        }
    }
