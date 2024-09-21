import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, TypeVar, Union

import yaml
from supabase import create_client

from config.config import config
from mini.core.logger import get_logger
from mini.database.models import TABLE_MODEL_MAP, TableModel

logger = get_logger(__name__)
T = TypeVar("T", bound=TableModel)


class DatabaseManager:
    def __init__(self) -> None:
        self.supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    def insert(self, table_name: str, item: TableModel) -> TableModel:
        item_dict = item.model_dump()

        # Generate UUID for id if not specified
        if "id" not in item_dict or item_dict["id"] is None:
            item_dict["id"] = str(uuid.uuid4())

        data, _ = self.supabase.table(table_name).insert(item_dict).execute()
        return type(item)(**data[1][0]) if data and data[1] else None

    def update(
        self,
        table_name: str,
        update_data: Dict[str, Any],
        condition_key: str,
        condition_value: Any,
    ) -> TableModel:
        # Remove any None values from the update_data
        update_data = {k: v for k, v in update_data.items() if v is not None}

        query = self.supabase.table(table_name).update(update_data)

        if not condition_key or not condition_value:
            raise ValueError(
                "Both condition_key and condition_value are required for update operation"
            )

        query = query.eq(condition_key, condition_value)

        data, _ = query.execute()
        if not data or not data[1]:
            raise ValueError(f"No data returned for update on {table_name}")

        model_class = TABLE_MODEL_MAP[table_name]
        return model_class(**data[1][0])

    def get_row(
        self,
        table_name: str,
        conditions: Dict[str, any],
        order_by: Optional[str] = None,
        order_desc: Optional[bool] = None,
    ) -> Optional[TableModel]:
        query = self.supabase.table(table_name).select("*")

        for key, value in conditions.items():
            if value is None:
                query = query.is_(key, value)
            else:
                query = query.eq(key, value)

        if order_by:
            query = query.order(order_by, desc=order_desc)

        data, _ = query.limit(1).execute()

        if data and data[1]:
            model_class = TABLE_MODEL_MAP[table_name]
            return model_class(**data[1][0])
        return None

    def get_multiple_rows(
        self,
        table_name: str,
        max_rows: int = 10,
        from_time: Optional[datetime] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
        conditions: Optional[Dict] = None,
        **kwargs,
    ) -> List[TableModel]:
        query = self.supabase.table(table_name).select("*")

        if conditions:
            for key, value in conditions.items():
                query = query.eq(key, value)

        for key, value in kwargs.items():
            query = query.eq(key, value)

        if from_time is not None:
            query = query.gte("created_at", from_time.isoformat())

        query = query.order(order_by, desc=order_desc).limit(max_rows)

        response = query.execute()

        if hasattr(response, "data") and isinstance(response.data, list):
            data = response.data
        else:
            logger.error(f"Unexpected response format from Supabase: {response}")
            return []

        model_class = TABLE_MODEL_MAP[table_name]
        return [model_class(**item) for item in data]

    def delete(self, table_name: str, conditions: Dict[str, Any]) -> bool:
        query = self.supabase.table(table_name).delete()
        for key, value in conditions.items():
            query = query.eq(key, value)
        result = query.execute()
        return len(result.data) > 0

    def query(
        self, table_name: str, *conditions: Union[Tuple[str, str], Tuple[str, str, str]]
    ) -> List[TableModel]:
        query = self.supabase.table(table_name).select("*")
        for condition in conditions:
            if len(condition) == 2:
                key, value = condition
                query = query.eq(key, value)
            elif len(condition) == 3:
                key, op, value = condition
                if op == ">":
                    query = query.gt(key, value)
                elif op == "<":
                    query = query.lt(key, value)
                elif op == ">=":
                    query = query.gte(key, value)
                elif op == "<=":
                    query = query.lte(key, value)
                elif op == "!=":
                    query = query.neq(key, value)
                else:
                    query = query.eq(key, value)
            else:
                logger.warning(f"Unexpected condition format: {condition}")

        data, _ = query.execute()
        model_class = TABLE_MODEL_MAP[table_name]
        return [model_class(**item) for item in data[1]] if data and data[1] else []

    def count_rows(
        self, table_name: str, conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        query = self.supabase.table(table_name).select("*", count="exact")

        if conditions:
            for key, value in conditions.items():
                if value is None:
                    query = query.is_(key, value)
                else:
                    query = query.eq(key, value)

        result = query.execute()
        return result.count

    def load_yaml_from_bucket(self, bucket_name: str, file_path: str) -> dict:
        """Load a YAML file from Supabase storage bucket and return as a dictionary."""
        response = self.supabase.storage.from_(bucket_name).download(file_path)
        file_content = response.decode("utf-8")
        return yaml.safe_load(file_content)

    def load_bucket(self, bucket_name: str) -> Dict[str, dict]:
        """Load all YAML files from a Supabase bucket."""
        files = self.supabase.storage.from_(bucket_name).list()

        yaml_data = {}
        for file_info in files:
            file_path = file_info["name"]
            if file_path.endswith(".yaml"):
                yaml_data[file_path] = self.load_yaml_from_bucket(
                    bucket_name, file_path
                )

        return yaml_data
