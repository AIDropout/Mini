from zootopia.core.schema import (
    RoomTableModel,
    MessageTableModel,
    AgentTableModel,
    SubscriptionTableModel,
    Tables,
)
from zootopia.services import SupabaseDB
from zootopia.controller.agent.action import ActionManager
from zootopia.memory import MemoryManager
from zootopia.core.logger import logger

class SubscribeManager:
    """
    Manages subscription-related operations for a chat room.
    """
    def __init__(
        self,
        database_service: SupabaseDB,
        action: ActionManager,
        memory: MemoryManager,
        room: RoomTableModel,
        agent: AgentTableModel
    ):
        self.database_service = database_service
        self.action = action
        self.memory = memory
        self.room = room
        self.agent = agent

    async def should_continue_conversation(self) -> bool:
        """
        Determine if the conversation should continue based on message count,
        subscription status, and active subscriptions.

        Returns:
            bool: True if the conversation should continue, False if it should stop.
        """
        if await self._has_active_subscription():
            return True

        # Get all messages for this room
        all_messages = self.database_service.get_multiple_rows(
            table_name=Tables.MESSAGES.value,
            conditions={"room_id": self.room.id},
            order_by=Tables.MESSAGES__created_at.value,
            order_desc=False,
        )

        # Count agent messages
        agent_message_count = sum(1 for message in all_messages if not message["from_user"])

        # Check if we need to send a subscription message
        if agent_message_count >= self.agent.free_msg_limit:
            if not self.room.subscribe_message_sent:
                await self._send_subscribe_message()
            return False
        
        return True

    async def _has_active_subscription(self) -> bool:
        """
        Check if the room has an active subscription.

        Returns:
            bool: True if there's an active subscription, False otherwise.
        """
        active_subscription = self.database_service.get_row(
            table_name=Tables.SUBSCRIPTIONS.value,
            conditions={
                Tables.SUBSCRIPTIONS__room_id.value: self.room.id,
                Tables.SUBSCRIPTIONS__ended_at.value: None
            }
        )
        return active_subscription is not None

    async def _send_subscribe_message(self):
        """
        Send a subscription message, store it, and update the room's status.
        """
        subscribe_message = (
            f"{self.agent.subscribe_message}\n\n"
            f"Subscribe here: {self.agent.subscribe_url}"
        )

        # Send the subscription message
        await self.action.handle_message_send(subscribe_message)

        # Store the subscription message
        self.memory.store_message(
            MessageTableModel(
                room_id=self.room.id,
                from_user=False,
                content=subscribe_message,
            )
        )

        # Update the room to indicate the subscription message was sent
        self.database_service.update(
            table_name=Tables.ROOMS.value,
            item=RoomTableModel(subscribe_message_sent=True),
            conditions=[(Tables.ROOMS__id.value, self.room.id)],
        )

        # Update the local room object
        self.room.subscribe_message_sent = True

        logger.info(f"Sent subscription message for room {self.room.id}")