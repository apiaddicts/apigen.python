from src.domain.parse_core.schemas.graphql_schema import GraphqlProjectSchema

class GraphQLStructure:
    @staticmethod
    def load_openapi_spec(project: GraphqlProjectSchema) -> dict:
        return project.openapi_spec
