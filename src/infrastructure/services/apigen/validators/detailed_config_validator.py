from typing import Dict, Any
from .project_validator import ProjectValidator
from .path_binding_validator import PathBindingValidator
from .model_validator import ModelsValidator
from .mapping_validator import MappingValidator


class DetailedConfigValidator:

    @staticmethod
    def validate(openapi_dict: dict) -> Dict[str, Any]:
        validation_results = {
            "all_valid": True,
            "validations": {
                "x-apigen-project": {"valid": False, "error": None},
                "x-apigen-models": {"valid": False, "error": None},
                "x-apigen-binding": {"valid": False, "error": None},
                "x-apigen-mapping": {"valid": False, "error": None}
            },
            "summary": {
                "total": 4,
                "passed": 0,
                "failed": 0
            }
        }

        models = []

        try:
            ProjectValidator.validate(openapi_dict)
            validation_results["validations"]["x-apigen-project"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        try:
            models = ModelsValidator.validate(openapi_dict)
            validation_results["validations"]["x-apigen-models"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-models"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-models"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        try:
            PathBindingValidator.validate(openapi_dict, models)
            validation_results["validations"]["x-apigen-binding"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-binding"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-binding"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        try:
            MappingValidator.validate(openapi_dict, models)
            validation_results["validations"]["x-apigen-mapping"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-mapping"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-mapping"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        return validation_results

    @staticmethod
    def validate_graphql(graphql_dict: dict) -> Dict[str, Any]:
        validation_results = {
            "all_valid": True,
            "validations": {
                "x-apigen-project": {"valid": False, "error": None}
            },
            "summary": {
                "total": 1,
                "passed": 0,
                "failed": 0
            }
        }

        try:
            ProjectValidator.validate_graphql(graphql_dict)
            validation_results["validations"]["x-apigen-project"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        return validation_results

    @staticmethod
    def validate_asyncapi(async_dict: dict) -> Dict[str, Any]:
        validation_results = {
            "all_valid": True,
            "validations": {
                "x-apigen-project": {"valid": False, "error": None},
                "x-apigen-models": {"valid": False, "error": None},
                "x-apigen-binding": {"valid": False, "error": None},
                "x-apigen-mapping": {"valid": False, "error": None}
            },
            "summary": {
                "total": 4,
                "passed": 0,
                "failed": 0
            }
        }

        # x-apigen-project: required when x-apigen-models exist (ASYNC-029)
        has_models = bool(async_dict.get("components", {}).get("x-apigen-models"))
        # Check both root level and info block for x-apigen-project
        project_dict = async_dict  # dict that contains x-apigen-project at top level
        has_project = "x-apigen-project" in async_dict
        if not has_project:
            info_dict = async_dict.get("info", {})
            if "x-apigen-project" in info_dict:
                has_project = True
                project_dict = info_dict
        try:
            if has_project:
                ProjectValidator.validate(project_dict)
            elif has_models:
                raise ValueError(
                    "x-apigen-project con data-driver es obligatorio cuando se usan x-apigen-models. "
                    "Añade x-apigen-project con data-driver (postgresql, mysql, mssql) al spec."
                )
            validation_results["validations"]["x-apigen-project"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-project"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        models = []
        model_attrs = {}
        try:
            models = ModelsValidator.validate(async_dict)
            # Build model_attrs lookup for property-level mapping validation
            apigen_models = async_dict.get("components", {}).get("x-apigen-models", {})
            for model_name, model_def in apigen_models.items():
                attrs = model_def.get("attributes", [])
                model_attrs[model_name] = [a["name"] for a in attrs if "name" in a]
            validation_results["validations"]["x-apigen-models"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-models"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-models"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        try:
            PathBindingValidator.validate_asyncapi(async_dict, models)
            validation_results["validations"]["x-apigen-binding"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-binding"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-binding"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        try:
            MappingValidator.validate_asyncapi(async_dict, models, model_attrs)
            validation_results["validations"]["x-apigen-mapping"]["valid"] = True
            validation_results["summary"]["passed"] += 1
        except ValueError as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-mapping"]["error"] = str(e)
            validation_results["summary"]["failed"] += 1
        except Exception as e:
            validation_results["all_valid"] = False
            validation_results["validations"]["x-apigen-mapping"]["error"] = f"Error inesperado: {str(e)}"
            validation_results["summary"]["failed"] += 1

        return validation_results
