import json
import tempfile
from graphql import GraphQLError

from ..validators.detailed_config_validator import DetailedConfigValidator

class GraphQLGenerator:

    def generate(self, content: str) -> str:
        from src.infrastructure.services.validators.graphql_validator_service import GraphQLValidatorService
        from src.domain.parse_core.parsers.graphql_parser import GraphqlParser

        spec = content
        validation_result = DetailedConfigValidator.validate_graphql(spec)

        if not validation_result["all_valid"]:
            return validation_result

        output_dir = tempfile.mkdtemp(prefix="graphql_project_")
        graphql_project_parser = GraphqlParser(GraphQLValidatorService())
        graphql_project_parser.load_definition(content)
        graphql_project_structure = graphql_project_parser.parse().model_dump()
        with open(f"{output_dir}/project.json", "w") as json_file:
            json.dump(graphql_project_structure, json_file)

        return output_dir


    def _parse_spec(self, raw_bytes: bytes):
        try:
            return raw_bytes.decode("utf-8")
        except GraphQLError as e:
            raise ValueError(f"SDL GraphQL inválido: {str(e)}")
