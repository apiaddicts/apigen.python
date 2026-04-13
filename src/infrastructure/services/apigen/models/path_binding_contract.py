from pydantic import BaseModel
from typing import Dict

class PathBindingContract(BaseModel):
    model: str
    params: Dict[str, str]

    @classmethod
    def from_raw(cls, raw: dict):
        if "model" not in raw:
            raise ValueError("x-apigen-binding requiere la propiedad 'model'")

        model = raw["model"]
        params = {k: v for k, v in raw.items() if k != "model"}

        if not params:
            raise ValueError("x-apigen-binding debe incluir al menos un path param")

        return cls(model=model, params=params)
