from zootopia.core.schema import (
    Room,
    Message,
    Agent,
    Tables,
    User,
)
from zootopia.manager.database import DatabaseManager
from zootopia.controller.agent.modules.action import ActionModule
from zootopia.controller.agent.modules.memory import MemoryModule
from zootopia.core.logger import logger
from zootopia.core.error import error_handler
from zootopia.controller.agent.modules.base import AgentModule


class SubscribeModule(AgentModule):
    """
    Manages subscription-related operations for a chat room.
    """

    def __init__(
        self,
        database_manager: DatabaseManager,
        action_module: ActionModule,
        memory_module: MemoryModule,
    ):
        super().__init__(database_manager)
        self.action_module = action_module
        self.memory_module = memory_module

    @error_handler("SubscribeManager")
    async def should_continue_conversation(self) -> dict:
        """
        Determine if the conversation should continue based on subscription status,
        message count, and whether subscriptions are enabled.

        Returns:
            dict: A dictionary containing relevant information and whether to continue.
        """
        result = {
            "continue": True,
            "subscribe_enabled": self.agent.subscribe_enabled,
            "has_active_subscription": False,
            "agent_message_count": 0,
            "free_msg_limit": self.agent.free_msg_limit,
            "subscribe_msg_sent": self.room.subscribe_msg_sent,
        }

        # Always get the message count, regardless of subscription status
        result["agent_message_count"] = await self._get_agent_message_count()

        if not self.agent.subscribe_enabled:
            return result

        result["has_active_subscription"] = self.user.subscription_status == "active"
        if result["has_active_subscription"]:
            return result

        # Check if we need to send a subscription message
        if result["agent_message_count"] >= self.agent.free_msg_limit:
            if not self.room.subscribe_msg_sent:
                await self._send_subscribe_message()
                result["subscribe_msg_sent"] = True
            result["continue"] = False

        return result

    @error_handler("SubscribeManager")
    async def _get_agent_message_count(self) -> int:
        """
        Get the number of agent messages in the room using a direct count query.

        Returns:
            int: The count of agent messages.
        """
        count = self.database_manager.count_rows(
            table_name=Tables.MESSAGES.value,
            conditions={
                Tables.MESSAGES__room_id.value: self.room.id,
                Tables.MESSAGES__sender_id.value: self.agent.id,
            },
        )
        logger.info(f"Agent message count in room {self.room.id}: {count} 🟡🟡🟡")
        return count

    @error_handler("SubscribeManager")
    async def _send_subscribe_message(self):
        """
        Send a subscription message, store it, and update the room's status.
        """
        subscribe_message = (
            f"{self.agent.subscribe_msg}\n\n"
            f"Subscribe here: {self.agent.subscribe_url}"
        )

        # Send the subscription message
        await self.action_module.handle_message_send(subscribe_message)

        # Store the subscription message
        self.database_manager.insert(
            Tables.MESSAGES.value,
            Message(
                room_id=self.room.id,
                sender_id=self.agent.id,
                content=subscribe_message,
            ),
        )

        # Update the room to indicate the subscription message was sent
        response = (
            self.database_manager.supabase.table(Tables.ROOMS.value)
            .update({Tables.ROOMS__subscribe_msg_sent.value: True})
            .eq(Tables.ROOMS__id.value, self.room.id)
            .execute()
        )

        # Update the local room object
        self.room.subscribe_msg_sent = True

        logger.info(f"Sent subscription message for room {self.room.id}")
