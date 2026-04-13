from enum import Enum


class DataDriver(Enum):
    MYSQL = "mysql"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    S3 = "s3"
    MSSQL = "mssql"


class EndpointMethodEnum(Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"


class AttributeTypeEnum(Enum):
    ARRAY = "Array"
    STRING = "String"
    BOOLEAN = "Boolean"
    DOUBLE = "Double"
    FLOAT = "Float"
    BIGDECIMAL = "BigDecimal"
    INTEGER = "Integer"
    LONG = "Long"
    BIGINTEGER = "BigInteger"
    LOCALDATE = "LocalDate"
    LOCALDATETIME = "LocalDateTime"
    ZONEDDATETIME = "ZonedDateTime"
    OFFSETDATETIME = "OffsetDateTime"
    INSTANT = "Instant"


class GRAPHQLBuiltInTypesEnum(Enum):
    string = "String"
    id = "ID"
    boolean = "Boolean"
    float = "Float"
    int = "Int"
