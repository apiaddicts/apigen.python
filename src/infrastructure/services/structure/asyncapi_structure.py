from src.domain.parse_core.schemas.asyncapi_schema import AsyncApiProjectSchema

class AsyncAPIStructure:
    @staticmethod
    def load_openapi_spec(project: AsyncApiProjectSchema) -> dict:
        return project.openapi_spec
