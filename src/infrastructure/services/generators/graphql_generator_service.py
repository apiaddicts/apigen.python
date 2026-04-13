import os
import logging
from typing import Union, Dict, Any
from ..apigen.generators.generator import GeneratorService

logger = logging.getLogger(__name__)

class GraphQLGeneratorService:
    @staticmethod
    def generate(content: str) -> Union[str, Dict[str, Any]]:
        generator_service = GeneratorService()
        result = generator_service.transform_spec(content)


        return result
