from zootopia.core.schema.tables import (
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
from dataclasses import dataclass
from zootopia.core.schema.subscription import SubscriptionStatus


@dataclass
class ConversationStatus:
    continue_conversation: bool
    subscribe_enabled: bool
    user_is_subscribed: bool
    agent_messages_in_room_count: int
    free_msg_limit: int
    subscribe_msg_sent: bool

    def __repr__(self) -> str:
        return (
            f"ConversationStatus("
            f"continue_conversation={self.continue_conversation}, "
            f"subscribe_enabled={self.subscribe_enabled}, "
            f"user_is_subscribed={self.user_is_subscribed}, "
            f"agent_messages_in_room_count={self.agent_messages_in_room_count}, "
            f"free_msg_limit={self.free_msg_limit}, "
            f"subscribe_msg_sent={self.subscribe_msg_sent})"
        )


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
    async def should_continue_conversation(self) -> ConversationStatus:
        """
        Determine if the conversation should continue based on subscription status,
        message count, and whether subscriptions are enabled.

        Returns:
            dict: A dictionary containing relevant information and whether to continue.
        """
        agent_messages_in_room_count = await self._get_agent_message_count()

        status = ConversationStatus(
            continue_conversation=True,
            subscribe_enabled=self.agent.subscribe_enabled,
            user_is_subscribed=False,
            agent_messages_in_room_count=agent_messages_in_room_count,
            free_msg_limit=self.agent.free_msg_limit,
            subscribe_msg_sent=self.room.subscribe_msg_sent,
        )

        if not status.subscribe_enabled:
            return status

        status.user_is_subscribed = self._check_user_is_subscribed()

        if (
            not status.user_is_subscribed
            and agent_messages_in_room_count >= status.free_msg_limit
        ):
            status.continue_conversation = False
            if not status.subscribe_msg_sent:
                await self._send_subscribe_message()
                status.subscribe_msg_sent = True

        return status

    def _check_user_is_subscribed(self) -> bool:
        """Check if the user has an active subscription."""
        subscription = self.database_manager.get_row(
            Tables.SUBSCRIPTIONS,
            {
                Tables.SUBSCRIPTIONS__user_id: self.user.id,
                Tables.SUBSCRIPTIONS__status: SubscriptionStatus.ACTIVE,
            },
        )
        return subscription is not None

    @error_handler("SubscribeManager")
    async def _get_agent_message_count(self) -> int:
        """
        Get the number of agent messages in the room using a direct count query.

        Returns:
            int: The count of agent messages.
        """
        count = self.database_manager.count_rows(
            table_name=Tables.MESSAGES,
            conditions={
                Tables.MESSAGES__room_id: self.room.id,
                Tables.MESSAGES__sender_id: self.agent.id,
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
            Tables.MESSAGES,
            Message(
                room_id=self.room.id,
                sender_id=self.agent.id,
                content=subscribe_message,
            ),
        )

        # Update the room to indicate the subscription message was sent
        self.room.subscribe_msg_sent = True
        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__subscribe_msg_sent: True},
            condition_key=Tables.ROOMS__id,
            condition_value=self.room.id,
        )

        logger.info(f"Sent subscription message for room {self.room.id}")
