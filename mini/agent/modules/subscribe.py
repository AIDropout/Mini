from dataclasses import dataclass

from config.config import config
from mini.agent.modules.action import ActionModule
from mini.agent.modules.base import AgentModule
from mini.agent.modules.memory.service import MemoryModule
from mini.core.logger import get_logger
from mini.payment.stripe.models import SubscriptionStatus
from mini.database.models import Agent, Message, Room, Tables, User
from mini.database.database import DatabaseManager

logger = get_logger(__name__)


@dataclass
class ConversationStatus:
    continue_conversation: bool
    user_is_subscribed: bool
    agent_messages_in_room_count: int
    free_msg_limit: int
    subscribe_msg_sent: bool

    def __repr__(self) -> str:
        return (
            f"ConversationStatus("
            f"continue_conversation={self.continue_conversation}, "
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
    ):
        super().__init__(database_manager)
        self.action_module = action_module

    def should_continue_conversation(self) -> ConversationStatus:
        """
        Determine if the conversation should continue based on subscription status,
        message count, and whether subscriptions are enabled.

        Returns:
            dict: A dictionary containing relevant information and whether to continue.
        """
        agent_messages_in_room_count = self._get_agent_message_count()

        status = ConversationStatus(
            continue_conversation=True,
            user_is_subscribed=False,
            agent_messages_in_room_count=agent_messages_in_room_count,
            free_msg_limit=self.agent.free_msg_limit,
            subscribe_msg_sent=self.room.subscribe_msg_sent,
        )

        status.user_is_subscribed = self._check_user_is_subscribed()

        if (
            not status.user_is_subscribed
            and agent_messages_in_room_count >= status.free_msg_limit
        ):
            status.continue_conversation = False
            if not status.subscribe_msg_sent:
                self._send_subscribe_message()
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

    def _get_agent_message_count(self) -> int:
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

    def _send_subscribe_message(self):
        """
        Send a subscription message, store it, and update the room's status.
        """
        subscribe_message = (
            f"{self.agent.subscribe_msg}\n" f"{config.FRONTEND_URL}/subscribe"
        )

        # Send the subscription message
        self.action_module.send_message(text=subscribe_message)

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
            {
                Tables.ROOMS__subscribe_msg_sent: True,
            },
            condition_key=Tables.ROOMS__id,
            condition_value=self.room.id,
        )

        logger.info(f"Sent subscription message for room {self.room.id}")
