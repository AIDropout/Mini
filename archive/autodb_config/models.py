
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Type, Union

from pydantic import BaseModel, Field

class SupabaseConfig(BaseModel):
    URL: str
    KEY: str


class TableType(Enum):
    ROW = "row"
    COL = "column"


class DataType(Enum):
    LIST = "list"
    JSON = "json"
    DICT = "json"
    BOOL = "boolean"
    STR = "string"
    INT = "integer"
    TIMESTAMP = "timestamp"


class DatabaseColumn(BaseModel):
    name: str
    datatype: DataType
    description: str


class DatabaseTable(BaseModel):
    name: str
    table_type: TableType
    description: str
    llm_control: bool
    columns: list[DatabaseColumn]


class AutoDBConfig(BaseModel):
    database_tables: list[DatabaseTable]
    intent_llm_config: LLMConfig


class DataLocation(BaseModel):
    table: str
    column: Optional[str]


class DataAction(BaseModel):
    data_location: DataLocation
    data: dict


class _TableIDConfig(BaseModel):
    USER: str
    GAUTH: str
    MESSAGE: str


class _UserIDConfig(BaseModel):
    TELEGRAM: str
    EMAIL: str


class ConstantIDConfig(BaseModel):
    TABLE_IDS: _TableIDConfig
    USER_IDS: _UserIDConfig
    ID_COLUMN_NAME: str

class GAuthTable(BaseModel):
    access_token: str
    refresh_token: str
    token_expiry: Optional[str] = None
    token_uri: str
    user_agent: Optional[str] = None


# class UserTable(BaseModel):
#     username: Optional[str] = None
#     telegram_id: Optional[int] = None
#     email_id: Optional[str] = None