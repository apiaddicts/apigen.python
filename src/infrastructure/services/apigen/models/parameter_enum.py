from enum import Enum

class ApigenProps(str, Enum):
    X_APIGEN_BINDING = "x-apigen-binding"
    X_APIGEN_MAPPING = "x-apigen-mapping"
    X_APIGEN_PROJECT = "x-apigen-project"
    X_APIGEN_MODELS  = "x-apigen-models"

    COMPONENTS = "components"
    SCHEMAS = "schemas"
    MODEL = "model"
    MESSAGES = "messages"