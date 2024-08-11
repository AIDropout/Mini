from datetime import datetime
from functools import wraps
from typing import List, Optional, TypeVar, Dict, Tuple, Union, Any, Callable
from supabase import create_client
from zootopia.core.logger import logger
from zootopia.core.config import config
from zootopia.core.schema import TableModel
from zootopia.core.schema.table import TABLE_MODEL_MAP
from zootopia.core.error import error_handler

T = TypeVar("T", bound=TableModel)


# TODO: add tests
class SupabaseDB:
    def __init__(self) -> None:
        self.supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

    @error_handler("Supabase")
    def insert(self, table_name: str, item: TableModel) -> TableModel:
        # Removes 'id' field, since Supabase auto-increments
        item_dict = item.model_dump(exclude={"id"})
        data, _ = self.supabase.table(table_name).insert(item_dict).execute()
        return type(item)(**data[1][0]) if data and data[1] else None

    @error_handler("Supabase")
    def update(
        self,
        table_name: str,
        item: TableModel,
        condition_key: str,
        condition_value: Any,
    ) -> TableModel:
        query = self.supabase.table(table_name).update(item.model_dump())

        if not condition_key or not condition_value:
            raise ValueError(
                "Both condition_key and condition_value are required for update operation"
            )

        query = query.eq(condition_key, condition_value)

        data, _ = query.execute()
        return type(item)(**data[1][0]) if data and data[1] else None

    @error_handler("Supabase")
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

    @error_handler("Supabase")
    def get_multiple_rows(
        self,
        table_name: str,
        max_rows: int = 10,
        from_time: Optional[datetime] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
        conditions: Optional[Dict] = None,
        **kwargs,
    ) -> List[Dict]:
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

        return data

    @error_handler("Supabase")
    def delete(self, table_name: str, *conditions) -> bool:
        query = self.supabase.table(table_name).delete()
        for key, value in conditions:
            query = query.eq(key, value)
        data, _ = query.execute()
        return bool(data and data[1])

    @error_handler("Supabase")
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

    @error_handler("Supabase")
    def count_rows(
        self,
        table_name: str,
        conditions: Optional[Dict[str, Any]] = None
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