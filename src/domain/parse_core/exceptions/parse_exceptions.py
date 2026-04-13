from typing import Any


class BaseParseException(Exception):
    def __init__(self, *args, message: str = None, context: Any = None):
        if not args and message:
            args = (message,)
        super().__init__(*args)
        self.message = message
        self.context = context


class InvalidContentsException(BaseParseException): ...


class InvalidOpenAPIDefinitionException(BaseParseException): ...


class InvalidModelDefinitionException(BaseParseException): ...


class MissingProjectDefinitionException(BaseParseException): ...
