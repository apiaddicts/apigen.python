from .project_validator import ProjectValidator
from .path_binding_validator import PathBindingValidator
from .model_validator import ModelsValidator
from .mapping_validator import MappingValidator

class ConfigValidator:
    @staticmethod
    def validate(openapi_dict: dict):
        ProjectValidator.validate(openapi_dict)
        models = ModelsValidator.validate(openapi_dict)
        PathBindingValidator.validate(openapi_dict, models)
        MappingValidator.validate(openapi_dict, models)
