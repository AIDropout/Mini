from mini.server.celery import celery_app as app
from datetime import time, timedelta, datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from celery import group
import math
import json
import random

from config.config import config
from mini.core.enums import MessageTaskType, MessagingProviderType
from mini.core.logger import get_logger
from mini.database.database import DatabaseManager
from mini.database.models import Tables, Room
from mini.database.tables.room_service import RoomTableService
from mini.utils.time import TimeManager


logger = get_logger(__name__)


class ProactiveService:
    """Proactive service that handles proactive message sending"""

    def __init__(
        self,
        database_manager: DatabaseManager,
        system_time_manager: TimeManager,
        room_service: RoomTableService,
    ) -> None:
        self.database_manager = database_manager
        self.system_time_manager = system_time_manager
        self.room_service = room_service
        self.breakpoints = [
            {"proactivity": 0.1, "hours": 432},    # 18 days
            {"proactivity": 0.2, "hours": 336},    # 14 days
            {"proactivity": 0.3, "hours": 240},    # 10 days
            {"proactivity": 0.4, "hours": 144},    # 6 days
            {"proactivity": 0.5, "hours": 96},     # 4 days
            {"proactivity": 0.6, "hours": 60},     # 60 hours
            {"proactivity": 0.7, "hours": 36},     # 36 hours
            {"proactivity": 0.8, "hours": 18},     # 18 hours
            {"proactivity": 0.9, "hours": 6},      # 6 hours
            {"proactivity": 1.0, "hours": 0.5}     # 30 minutes
        ]

    def send_proactive_messages(self, is_local: bool) -> None:
        """
        Gets all proactive rooms. For each room, does a celery task
        """

        # Should not send any at night
        if self._is_system_night():
            logger.info("Is night. Skipping proactive processing")
            return

        # Get proactive rooms
        logger.info("heyyy")
        limit = 5  # Example: Limit to 10 rooms

        room_ids = self._fetch_rooms(limit, is_local)

        logger.info(room_ids)
        logger.info(app.tasks)

        # New group for send_message tasks
        from mini.server.celery.tasks.send_message import send_message
        send_message_group = group(
            send_message.s(
                MessagingProviderType.BIRD.value,
                id,
                MessageTaskType.RESPONSE.value
            ) for id in room_ids
        )

        # Send messages
        send_message_group.delay()

    def _is_system_night(self) -> bool:
        current_datetime = self.system_time_manager.get_user_datetime()
        est_datetime = current_datetime.astimezone(ZoneInfo("America/New_York"))
        if est_datetime.time() in (time(19, 0), time(7, 0)):
            return True
        return False
    
    def _fetch_rooms(self, limit: int, is_local: bool) -> List[str]:
        proactivity_hours_json = json.dumps(self.breakpoints)
        
        sql = f"""
        WITH proactivity_hours AS (
            SELECT * FROM json_to_recordset('{proactivity_hours_json}'::json)
            AS x(proactivity FLOAT, hours FLOAT)
        ),
        room_urgency AS (
            SELECT 
                r.id,
                r.agent_proactivity,
                CASE
                    WHEN r.agent_proactivity = 0 THEN 0
                    ELSE LEAST(
                        EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - r.last_msg_sent_at)) / 3600 / 
                        (SELECT hours FROM proactivity_hours WHERE proactivity <= r.agent_proactivity ORDER BY proactivity DESC LIMIT 1),
                        1
                    )
                END AS urgency
            FROM rooms r
            WHERE r.agent_proactivity > 0 AND r.agent_proactivity <= 1
        )
        SELECT json_build_object('id', id) AS result
        FROM room_urgency
        WHERE urgency > 0  -- Exclude rooms with 0 proactivity
        ORDER BY urgency DESC, agent_proactivity DESC
        LIMIT {limit}
        """

        try:
            response = self.database_manager.supabase.rpc(
                "execute_sql", {"sql": sql}
            ).execute()
            return [item['id'] for item in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error in _fetch_rooms: {e}", exc_info=True)
            return []