import logging
import re
import subprocess
import os
import tempfile
import yaml
import base64
from typing import Dict, Any, List, Optional

from src.infrastructure.services.validators.base_spec_parser_service import BaseSpecParserService

logger = logging.getLogger(__name__)


class AsyncAPIParserService(BaseSpecParserService):
    """Servicio para validar especificaciones AsyncAPI 3.0 usando AsyncAPI CLI oficial"""

    SUPPORTED_VERSIONS = ['3.0.0']

    _NOISE_PATTERNS = [
        'FATAL: NODE_ENV',
        'node-config/wiki',
        'Strict-Mode',
        'NODE_CONFIG_STRICT_MODE',
        'SUPPRESS_NO_CONFIG_WARNING',
        'anonymously tracks command',
        'asyncapi config analytics',
    ]

    _POSITION_RE = re.compile(r'^\d+:\d+$')

    def _get_spec_name(self) -> str:
        return "AsyncAPI"

    def _validate_with_cli(self, file_path: str) -> Dict[str, Any]:
        try:
            if not os.path.exists(file_path):
                raise ValueError(f"Archivo no encontrado: {file_path}")

            cli_home = tempfile.mkdtemp(prefix="asyncapi_cli_")
            env = {
                **os.environ,
                "HOME": cli_home,
                "SUPPRESS_NO_CONFIG_WARNING": "1",
                "NODE_CONFIG_STRICT_MODE": "0",
            }

            env.pop("NODE_ENV", None)
            try:
                result = subprocess.run(
                    ["asyncapi", "validate", file_path],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env=env
                )
            finally:
                import shutil
                shutil.rmtree(cli_home, ignore_errors=True)

            if result.returncode == 0:
                logger.info(f"AsyncAPI CLI: Archivo válido - {file_path}")
                return {
                    "valid": True,
                    "cli_output": result.stdout.strip(),
                    "errors": []
                }
            else:
                logger.warning(f"AsyncAPI CLI: Archivo inválido - {file_path}")
                raw_output = result.stderr.strip() if result.stderr else result.stdout.strip()
                parsed_errors = self._parse_cli_errors(raw_output)
                return {
                    "valid": False,
                    "cli_output": raw_output,
                    "errors": parsed_errors
                }

        except FileNotFoundError:
            raise RuntimeError(
                "AsyncAPI CLI no está instalado globalmente. Ejecuta: npm install -g @asyncapi/cli@5.0.5"
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout: AsyncAPI CLI tardó demasiado en responder")
        except Exception as e:
            raise RuntimeError(f"Error al ejecutar AsyncAPI CLI: {str(e)}")

    def _parse_cli_errors(self, cli_output: str) -> List[str]:
        parsed_errors = []
        for line in cli_output.splitlines():
            if any(pattern in line for pattern in self._NOISE_PATTERNS):
                continue

            parts = re.split(r'\s{2,}', line.strip())
            if len(parts) >= 3 and self._POSITION_RE.match(parts[0]):
                position = parts[0]
                description = parts[-2] if len(parts) >= 4 else parts[1]
                path = parts[-1]
                parsed_errors.append(f"Line {position} — {path}: {description}")

        return parsed_errors

    def _validate_spec(self, file_path: str) -> Dict[str, Any]:
        errors = []
        asyncapi_version = self.spec_dict.get('asyncapi', '')
        title = self.spec_dict.get('info', {}).get('title')


        if not asyncapi_version:
            return {
                "valid": False,
                "version": None,
                "title": title,
                "errors": ["El archivo no contiene la clave 'asyncapi'. Asegúrate de que sea una especificación AsyncAPI válida."]
            }

        cli_result = self._validate_with_cli(file_path)

        if not cli_result["valid"]:
            if cli_result["errors"]:
                errors.extend(cli_result["errors"])
            else:
                errors.append(f"AsyncAPI CLI validation failed: {cli_result['cli_output']}")

        if errors:
            logger.warning(f"Especificación AsyncAPI inválida: {len(errors)} errores encontrados")
            return {
                "valid": False,
                "version": asyncapi_version if asyncapi_version else None,
                "title": title,
                "errors": errors
            }

        logger.info("Especificación AsyncAPI 3.0 validada exitosamente con AsyncAPI CLI")

        # Convertir spec_dict a YAML
        yaml_content = yaml.dump(self.spec_dict, default_flow_style=False, allow_unicode=True)

        return {
            "valid": True,
            "version": asyncapi_version,
            "title": title,
            "content": yaml_content,
            "errors": []
        }

    def validate(self, file_path: Optional[str] = None, content: Optional[str] = None,
                 format_type: str = 'yaml') -> Dict[str, Any]:
        temp_file = None

        try:
            if content:
                suffix = '.yaml' if format_type == 'yaml' else '.json'
                with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False, encoding='utf-8') as f:
                    f.write(content)
                    temp_file = f.name

                file_path = temp_file
                logger.info("Contenido guardado en archivo temporal para validación")

            if not file_path:
                return {
                    "valid": False,
                    "version": None,
                    "title": None,
                    "errors": ["Debe proporcionar file_path o content"]
                }

            self.spec_dict = self._load_file(file_path)
            result = self._validate_spec(file_path)
            return result

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return {
                "valid": False,
                "version": None,
                "title": None,
                "errors": [str(e)]
            }
        except RuntimeError as e:
            logger.error(f"Error del AsyncAPI CLI: {str(e)}")
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
        finally:
            if temp_file and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                    logger.debug(f"Archivo temporal eliminado: {temp_file}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal: {e}")
