from pydantic import BaseModel, Field
from typing import List, Optional


class GraphqlContract(BaseModel):
    schemas: dict = Field(..., description="The graphql schemas of the project")
    resolvers: dict = Field(..., description="The graphql resolvers of the project")
