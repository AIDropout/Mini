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
    """
    Service Class that interacts with the Sessions Table.
    """

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
        - This + "update_active_session" is called when a user or agent sends a message
        """
        return self._get_active_session(room_id) or self._start_session(room_id)

    def _get_active_session(self, room_id: str) -> Session:
        """
        Get latest active session

        TODO: change to when last_updated is most recent
        """
        return self.database_manager.get_row(
            table_name=Tables.SESSIONS,
            conditions={
                Tables.SESSIONS__room_id: room_id,
                Tables.SESSIONS__ended_at: None,
            },
        )

    def _start_session(self, room_id: str) -> Session:
        """
        Starts a session.
        """
        return self.database_manager.insert(Tables.SESSIONS, Session(room_id=room_id))

    def update_active_session(self, session: Session) -> Session:
        """
        Increment session message count and update last msg timestamp
        - Called when a message is sent
        """
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
    
    def get_recent_processed_sessions(self, count: int) -> Optional[List[Session]]:
        """
        Returns list of most recently processed Session objects
        - Called before a message is to be generated
        """
        pass
    
    """The following are methods run by cron:"""

    def process_stale_sessions(self) -> bool:
        """
        Called by Beat every x minutes
        """
        sessions = self._get_stale_sessions()

        for session in sessions:
            self._end_session(session.id)
            # TODO: add Celery task to process session (i.e. process memory, user preferences)
            self._mark_session_processed(session.id)

    def _get_stale_sessions(self) -> List[Session]:
        """
        Define criteria here:

        - At least 20 messages have been sent
        - AND 12 hours have passed since active session was last updated
        """
        pass

    def _end_session(self, session_id: str):
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

    def _mark_session_processed(self, session_id) -> Session:
        """
        Updates "processed" field to True
        """
        self.database_manager.update(
            table_name=Tables.SESSIONS,
            update_data={
                Tables.SESSIONS__processed: True,
            },
            condition_key=Tables.SESSIONS__id,
            condition_value=session_id,
        )
