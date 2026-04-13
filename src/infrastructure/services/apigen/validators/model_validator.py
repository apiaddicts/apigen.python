from ..models.model_contract import ModelContract
from ..models.parameter_enum import ApigenProps

class ModelsValidator:
    @staticmethod
    def validate(openapi_dict: dict) -> list[str]:
        components = openapi_dict.get(ApigenProps.COMPONENTS, {})
        raw_models = components.get(ApigenProps.X_APIGEN_MODELS)

        if not raw_models:
            raise ValueError(
                "La especificación AsyncAPI no contiene 'x-apigen-models' en components. "
                "Defina los modelos de datos para la generación de código."
            )
        if not isinstance(raw_models, dict):
            raise ValueError("components.x-apigen-models debe ser un objeto map.")

        valid_models = []
        for model_name, model_def in raw_models.items():
            if not isinstance(model_name, str):
                raise ValueError("Los nombres de los modelos deben ser string.")
            try:
                ModelContract(**model_def)
            except Exception as e:
                raise ValueError(
                    f"Modelo '{model_name}' inválido en x-apigen-models: {e}"
                )

            valid_models.append(model_name)
        return valid_models
