import os
import logging
from typing import Union, Dict, Any
from ..apigen.generators.generator import AsyncAPIGenerator

logger = logging.getLogger(__name__)

class AsyncAPIGeneratorService:
    @staticmethod
    def generate(content: str, existing_project_dir: str = None) -> Union[str, Dict[str, Any]]:
        generator_service = AsyncAPIGenerator()
        result = generator_service.generate(
            content,
            existing_project_dir=existing_project_dir,
        )


        return result
