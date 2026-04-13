import re
from ..models.path_binding_contract import PathBindingContract
from ..models.parameter_enum import ApigenProps

class PathBindingValidator:
    @staticmethod
    def validate(open_api: dict, models: list[str]):
        paths = open_api.get("paths", {})
        for path, item in paths.items():
            if ApigenProps.X_APIGEN_BINDING in item:
                PathBindingValidator._validate(path, item[ApigenProps.X_APIGEN_BINDING], models)

    @staticmethod
    def _validate(path: str, raw_binding: dict, models: list[str]):
        if not raw_binding:
            return None

        if ApigenProps.MODEL not in raw_binding:
            raise ValueError(
                f"El path '{path}' define {ApigenProps.X_APIGEN_BINDING} pero no incluye la propiedad obligatoria {ApigenProps.MODEL}."
            )
        model = raw_binding.get(ApigenProps.MODEL)
        if model not in models:
            raise ValueError(
                f"Model '{model}' referenciado en el binding '{path}' no está definido en {ApigenProps.X_APIGEN_MODELS}."
            )
        expected_params = PathBindingValidator._extract_path_params(path)

        if len(expected_params) >= 2:
            binding = PathBindingContract.from_raw(raw_binding)
            PathBindingValidator._validate_params_exist(path, expected_params, binding)
            PathBindingValidator._validate_all_bound(path, expected_params, binding)
            PathBindingValidator._validate_format(path, binding)

    @staticmethod
    def _extract_path_params(path: str):
        return re.findall(r"{(.*?)}", path)

    @staticmethod
    def _validate_params_exist(path, expected, binding):
        for p in binding.params:
            if p not in expected:
                raise ValueError(
                    f"El parámetro '{p}' en {ApigenProps.X_APIGEN_BINDING} NO existe en el path '{path}'. "
                    f"Parámetros esperados: {expected}"
                )

    @staticmethod
    def _validate_all_bound(path, expected, binding):
        for p in expected:
            if p not in binding.params:
                raise ValueError(
                    f"El parámetro '{p}' del path '{path}' no está definido en {ApigenProps.X_APIGEN_BINDING}."
                )

    @staticmethod
    def _validate_format(path, binding):
        for param, value in binding.params.items():
            if not re.match(r"^[A-Za-z_]\w*\.[A-Za-z_]\w*$", value):
                raise ValueError(
                    f"Binding inválido '{value}' para el parámetro '{param}' en path '{path}'. "
                    "Formato esperado: <Model>.<field>."
                )

    @staticmethod
    def validate_asyncapi(async_dict: dict, models: list[str]):
        components = async_dict.get(ApigenProps.COMPONENTS, {})
        messages = components.get(ApigenProps.MESSAGES, {})
        for message_name, message_def in messages.items():
            binding = message_def.get(ApigenProps.X_APIGEN_BINDING)
            if not binding:
                continue
            action = binding.get("action", "")
            model = binding.get(ApigenProps.MODEL)
            # action: custom does not require a model (fire-and-forget, no DB)
            if action == "custom" and not model:
                continue
            if not model:
                raise ValueError(
                    f"Schema '{message_name}' has {ApigenProps.X_APIGEN_MAPPING} but no model defined."
                )
            if model not in models:
                raise ValueError(
                    f"Model '{model}' referenciado en el mapeo '{message_name}' no está definido en {ApigenProps.X_APIGEN_MODELS}."
                )
