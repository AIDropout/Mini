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

    def add_message(
        self, room_id: str, sender_id: str, content: str, session_id: str
    ) -> None:
        self.database_manager.insert(
            table_name=Tables.MESSAGES,
            item=Message(
                room_id=room_id,
                sender_id=sender_id,
                content=content,
                session_id=session_id,
            ),
        )

    def get_messages_in_session(self, session_id: str) -> List[Message]:
        messages = self.database_manager.get_multiple_rows(
            table_name=Tables.MESSAGES,
            max_rows=100,  # Set high
            order_by=Tables.MESSAGES__created_at,
            order_desc=True,
            conditions={Tables.MESSAGES__session_id: session_id},
        )

        return messages
    
    def get_user_message_count(self, user_id: str) -> int:
        return self.database_manager.count_rows(
            table_name=Tables.MESSAGES,
            conditions={
                Tables.MESSAGES__sender_id: user_id,
            },
        )
