from typing import List, Optional

from fastapi import HTTPException

from mini.core.logger import get_logger
from mini.database.models import Agent, Message, Room, Tables, Subscription, Message
from mini.database.database import DatabaseManager
from mini.messaging.providers.bird import BirdMessaging
from mini.payment.stripe.customer import CustomerManager
from mini.database.tables.user_service import UserTableService
from mini.database.tables.agent_service import AgentTableService

logger = get_logger(__name__)


class MessageTableService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        # customer_manager: CustomerManager,
        # user_table_service: UserTableService,
        # agent_table_service: AgentTableService,
    ):
        self.database_manager = database_manager
        # self.messaging_provider = BirdMessaging()
        # self.customer_manager = customer_manager
        # self.user_table_service = user_table_service
        # self.agent_table_service = agent_table_service

    def add_message(self, room_id: str, sender_id: str, content: str) -> None:
        self.database_manager.insert(
            table_name=Tables.MESSAGES,
            item=Message(
                room_id=room_id,
                sender_id=sender_id,
                content=content,
            ),
        )