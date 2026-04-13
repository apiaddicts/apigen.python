import json
import os
import re
import tempfile
import yaml
from typing import Dict, Any, Union, List, Tuple

from src.domain.parse_core.schemas.rest_schema import RESTProjectSchema
from src.infrastructure.services.structure.openapi_structure import OpenAPIStructure
from ..validators.detailed_config_validator import DetailedConfigValidator
from ..x_apigen_schema_reference import get_validation_error_response

try:
    import apigen_copier
    HAS_APIGEN_COPIER = True
except ImportError:
    HAS_APIGEN_COPIER = False


class OpenAPIGenerator:

    def _validate_spec(self, original_spec: str) -> Union[None, Dict[str, Any]]:
        """
        Validates the original OpenAPI spec string.
        Returns an error response dict if validation fails, otherwise None.
        """
        if not original_spec:
            return None

        try:
            try:
                spec_dict = json.loads(original_spec)
            except json.JSONDecodeError:
                spec_dict = yaml.safe_load(original_spec)
            
            validation_result = DetailedConfigValidator.validate(spec_dict)
            if not validation_result["all_valid"]:
                return get_validation_error_response(validation_result)
        except Exception:
            pass
        
        return None

    def _sanitize_routers(self, routers_dict):
        new_routers = {}
        for key, router in routers_dict.items():
            new_key = key.lstrip("/") if key.startswith("/") else key
            
            if router.mapping.startswith("/"):
                router.mapping = router.mapping.lstrip("/")
            
            if router.sub_routers:
                router.sub_routers = self._sanitize_routers(router.sub_routers)
            
            new_routers[new_key] = router
        return new_routers

    @staticmethod
    def _snake_to_camel(snake_str: str) -> str:
        """Convert snake_case to camelCase: category_id -> categoryId."""
        parts = snake_str.split("_")
        return parts[0] + "".join(p.capitalize() for p in parts[1:])

    def _collect_fk_info(self, project: RESTProjectSchema) -> Dict[str, List[Tuple[str, str, str]]]:
        """
        For each entity, collect FK relation info.
        Returns: { "EntityName": [(fk_id_field, fk_column, relation_attr_name), ...] }
        Example: { "Pet": [("categoryId", "category_id", "category"), ("ownerId", "owner_id", "owner")] }
        """
        fk_map = {}
        entities_data = project.model_dump(by_alias=True)
        entities = entities_data.get("entities", {})

        for entity_name, entity_data in entities.items():
            fk_list = []
            for attr in entity_data.get("attributes", []):
                if attr.get("type") == "Relation" and not attr.get("is-array", False):
                    persistence = attr.get("relational-persistence", {}) or {}
                    fk_column = persistence.get("column")
                    if fk_column:
                        fk_id_field = self._snake_to_camel(fk_column)
                        fk_list.append((fk_id_field, fk_column, attr["name"]))
            if fk_list:
                fk_map[entity_name] = fk_list
        return fk_map

    def _post_process_fk_ids(self, project: RESTProjectSchema, output_dir: str):
        """
        Post-process generated code to add FK ID fields to domain models and mappers.
        This ensures the API accepts flat FK IDs (e.g. categoryId: 1) in POST/PUT
        as defined in the input OpenAPI spec.
        """
        fk_map = self._collect_fk_info(project)
        if not fk_map:
            return

        project_slug = project.project.name.lower().replace(" ", "_").replace("-", "_")
        project_dir = os.path.join(output_dir, project_slug)
        if not os.path.isdir(project_dir):
            subdirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))]
            if subdirs:
                project_dir = os.path.join(output_dir, subdirs[0])
            else:
                return

        src_dir = os.path.join(project_dir, "src")
        if not os.path.isdir(src_dir):
            return

        for entity_name, fk_list in fk_map.items():
            entity_lower = entity_name.lower()
            self._patch_domain_model(src_dir, entity_lower, entity_name, fk_list)
            self._patch_mapper(src_dir, entity_lower, entity_name, fk_list)

    def _patch_domain_model(self, src_dir: str, entity_lower: str, _entity_name: str,
                            fk_list: List[Tuple[str, str, str]]):
        """Add FK ID fields (e.g. categoryId: Optional[int] = None) to domain model."""
        model_path = os.path.join(src_dir, "domain", "models", entity_lower,
                                  f"{entity_lower}_model.py")
        if not os.path.exists(model_path):
            return

        with open(model_path, "r") as f:
            content = f.read()

        lines = content.split("\n")
        new_lines = []
        for line in lines:
            new_lines.append(line)
            for fk_id_field, fk_column, relation_name in fk_list:
                pattern = rf"^\s+{re.escape(relation_name)}\s*:\s*Optional\[.*\]\s*=\s*None"
                if re.match(pattern, line):
                    indent = len(line) - len(line.lstrip())
                    fk_line = f"{' ' * indent}{fk_id_field}: Optional[int] = None"
                    new_lines.append("")
                    new_lines.append(fk_line)

        with open(model_path, "w") as f:
            f.write("\n".join(new_lines))

    def _patch_mapper(self, src_dir: str, entity_lower: str, _entity_name: str,
                      fk_list: List[Tuple[str, str, str]]):
        """Update mapper to handle FK IDs: prioritize flat FK ID over nested object."""
        mapper_path = os.path.join(src_dir, "infrastructure", "mappers", entity_lower,
                                   f"{entity_lower}_mapper.py")
        if not os.path.exists(mapper_path):
            return

        with open(mapper_path, "r") as f:
            content = f.read()

        for fk_id_field, fk_column, relation_name in fk_list:
            old_pattern = (
                rf"({re.escape(fk_column)}\s*=\s*)model\.{re.escape(relation_name)}\.id\s+"
                rf"if\s+model\.{re.escape(relation_name)}\s+else\s+None"
            )
            new_value = (
                rf"\g<1>model.{fk_id_field} if model.{fk_id_field} is not None "
                rf"else (model.{relation_name}.id if model.{relation_name} else None)"
            )
            content = re.sub(old_pattern, new_value, content)

            old_pattern2 = (
                rf"({re.escape(fk_column)}\s*=\s*)\(model\.{re.escape(relation_name)}\.id\s+"
                rf"if\s+model\.{re.escape(relation_name)}\s+else\s+None\)"
            )
            new_value2 = (
                rf"\g<1>(model.{fk_id_field} if model.{fk_id_field} is not None "
                rf"else (model.{relation_name}.id if model.{relation_name} else None))"
            )
            content = re.sub(old_pattern2, new_value2, content)

            to_domain_pattern = (
                rf"({re.escape(relation_name)}\s*=\s*entity\.{re.escape(relation_name)}\s*,)"
            )
            to_domain_replacement = (
                rf"\g<1>\n            {fk_id_field}=entity.{fk_column},"
            )
            content = re.sub(to_domain_pattern, to_domain_replacement, content)

        with open(mapper_path, "w") as f:
            f.write(content)

    def generate(self, project: RESTProjectSchema, original_spec: str = None, existing_project_dir: str = None) -> Union[str, Dict[str, Any]]:
        validation_error = self._validate_spec(original_spec)
        if validation_error:
            return validation_error

        output_dir = tempfile.mkdtemp(prefix="openapi_project_")
        
        project_json_path = os.path.join(output_dir, "project.json")
        if project.project.name.startswith("/"):
            project.project.name = project.project.name.lstrip("/")

        project.routers = self._sanitize_routers(project.routers)
        
        json_content = project.model_dump_json(indent=4, exclude_none=True, by_alias=True)
        
        with open(project_json_path, "w") as f:
            f.write(json_content)
        
        if HAS_APIGEN_COPIER:
            apigen_copier.generate_project(
                project_json_path,
                output_dir,
                existing_project_dir=existing_project_dir,
            )
            self._post_process_fk_ids(project, output_dir)
        else:
            raise ImportError("apigen_copier package is not installed. Cannot generate project structure. Please install it (e.g. pip install ../ods-data-generator-examples)")
        
        return output_dir
