from typing import List, Optional

from fastapi import HTTPException

from mini.core.logger import get_logger
from mini.database.models import (
    Tables,
    Session,
)
from mini.database.database import DatabaseManager
from mini.utils.time import TimeManager

logger = get_logger(__name__)


class SessionTableService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        system_time_manager: TimeManager,
    ):
        self.database_manager = database_manager
        self.system_time_manager = system_time_manager

    def get_or_start_active_session(self, room_id: str) -> Session:
        """
        Returns active session, or a new one if no active session
        """
        return self.get_active_session(room_id) or self.start_session(room_id)

    def get_active_session(self, room_id: str) -> Session:
        """
        Get latest active session
        """
        return self.database_manager.get_row(
            table_name=Tables.SESSIONS,
            conditions={
                Tables.SESSIONS__room_id: room_id,
                Tables.SESSIONS__ended_at: None,
            },
        )

    def start_session(self, room_id: str) -> Session:
        """
        Starts a session.
        """
        return self.database_manager.insert(Tables.SESSIONS, Session(room_id=room_id))

    def update_active_session(self, room_id: str) -> Session:
        """
        Increment session message count and update last msg timestamp
        """
        session = self.get_active_session(room_id)
        timestamp = self.system_time_manager.get_user_datetime()
        return self.database_manager.update(
            table_name=Tables.SESSIONS,
            update_data={
                Tables.SESSIONS__message_count: session.message_count + 1,
                Tables.SESSIONS__last_updated: timestamp,
            },
            condition_key=Tables.SESSIONS__id,
            condition_value=session.id,
        )
    
    def end_session(self, session_id: str):
        """
        Updates the ended_at field
        """
        timestamp = self.system_time_manager.get_user_datetime()
        self.database_manager.update(
            table_name=Tables.SESSIONS,
            update_data={
                Tables.SESSIONS__ended_at: timestamp,
            },
            condition_key=Tables.SESSIONS__id,
            condition_value=session_id,
        )
