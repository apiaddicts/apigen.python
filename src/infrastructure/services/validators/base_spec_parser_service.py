import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class BaseSpecParserService(ABC):
    """Clase base abstracta para servicios de validación de especificaciones (OpenAPI, AsyncAPI, etc.)"""

    def __init__(self):
        self.spec_dict: Dict[str, Any] = {}

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Carga un archivo YAML o JSON"""
        try:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return yaml.safe_load(file)
            elif file_path.endswith('.json'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            else:
                raise ValueError("El archivo debe ser YAML (.yaml, .yml) o JSON (.json)")

        except FileNotFoundError:
            raise ValueError(f"Archivo no encontrado: {file_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"Error al parsear YAML: {str(e)}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al cargar archivo: {str(e)}")

    def _load_string(self, content: str, format_type: str = 'yaml') -> Dict[str, Any]:
        """Carga una especificación desde un string"""
        try:
            if format_type.lower() == 'yaml':
                return yaml.safe_load(content)
            elif format_type.lower() == 'json':
                return json.loads(content)
            else:
                raise ValueError("format_type debe ser 'yaml' o 'json'")

        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Error al parsear contenido: {str(e)}")

    def _extract_metadata(self, version_key: str, title_path: tuple = ('info', 'title')) -> tuple:
        """Extrae versión y título de la especificación"""
        version = self.spec_dict.get(version_key, '')
        title = self.spec_dict
        for key in title_path:
            title = title.get(key, {}) if isinstance(title, dict) else None
        return version, title

    @abstractmethod
    def _validate_spec(self, file_path: str) -> Dict[str, Any]:
        """Método abstracto para validar la especificación según el estándar específico"""
        pass

    @abstractmethod
    def _get_spec_name(self) -> str:
        """Retorna el nombre de la especificación (OpenAPI, AsyncAPI, etc.)"""
        pass

    def validate(self, file_path: Optional[str] = None, content: Optional[str] = None,
                 format_type: str = 'yaml') -> Dict[str, Any]:
        """Método público para validar una especificación"""
        try:
            if file_path:
                self.spec_dict = self._load_file(file_path)
                logger.info(f"{self._get_spec_name()} cargado desde archivo: {file_path}")
            elif content:
                self.spec_dict = self._load_string(content, format_type)
                logger.info(f"{self._get_spec_name()} cargado desde string")
            else:
                return {
                    "valid": False,
                    "version": None,
                    "title": None,
                    "errors": ["Debe proporcionar file_path o content"]
                }

            result = self._validate_spec(file_path if file_path else content)
            return result

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return {
                "valid": False,
                "version": None,
                "title": None,
                "errors": [str(e)]
            }
        except Exception as e:
            logger.error(f"Error inesperado durante validación: {str(e)}")
            return {
                "valid": False,
                "version": None,
                "title": None,
                "errors": [f"Error inesperado: {str(e)}"]
            }
