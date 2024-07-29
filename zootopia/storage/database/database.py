from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from zootopia.core.schema import TableModel


class Database(ABC):
    @abstractmethod
    def insert(self, table_name: str, item: TableModel) -> TableModel:
        pass

    @abstractmethod
    def update(self, table_name: str, item: TableModel, *conditions) -> TableModel:
        pass

    @abstractmethod
    def get_row(self, table_name: str, *conditions) -> Optional[TableModel]:
        pass

    @abstractmethod
    def get_multiple_rows(
        self,
        table_name: str,
        max_rows: int = 10,
        from_time: Optional[datetime] = None,
        order_by: str = "created_at",
        order_desc: bool = True,
        *conditions
    ) -> List[TableModel]:
        pass

    @abstractmethod
    def delete(self, table_name: str, *conditions) -> bool:
        pass

    @abstractmethod
    def query(self, table_name: str, *conditions) -> List[TableModel]:
        pass
