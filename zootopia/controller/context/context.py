"""Class used to store utils needed for agent_controller logic"""

from zootopia.core.logger import logger
from typing import Tuple
from config.config import Config, SupabaseConfig, MessagingConfig
from zootopia.core.schema import Tables, AgentTableModel, RoomTableModel, UserTableModel
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.platform.platform import MessageProviderBase
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.platform.telegram.telegram import Telegram
from zootopia.platform.models import (
    BirdMetadata,
    MessageProvider,
    TelegramMetadata,
    ZootopiaMessage,
)
from zootopia.core.exceptions import AgentNotFoundError

class ContextManager:
    def __init__(self, request_body, supabase_config: SupabaseConfig, messaging_config: MessagingConfig):
        """
        1. Init database
        2. Init correct messaging service given the message
        3. Use messaging service to format it into a ZootopiaMessage object
        4. Use ZootopiaMessage to locate correct user, agent, and room
        """
        self.database: SupabaseDB = SupabaseDB.from_config(
            supabase_config
        )
        self.messaging_service: MessageProviderBase = self._create_messaging_provider(
            request_body, messaging_config
        )
        self.message: ZootopiaMessage = self.messaging_service.receive_message(
            request_body
        )
        self.user, self.agent = self._get_user_and_agent_from_db(self.message)
        self.room: RoomTableModel = self._get_or_create_room_from_db(
            self.user, self.agent
        )

    @classmethod
    def from_config(cls, request_body, config: Config) -> "ContextManager":
        supabase_config = config.DATABASE_CONFIG.SUPABASE
        messaging_config = config.MESSAGING_CONFIG
        return cls( 
            request_body, supabase_config, messaging_config
        )
    
    def __str__(self):
        return f"ContextManager(user={self.user}, agent={self.agent}, room={self.room}, message={self.message})"

    def _create_messaging_provider(
        self, request_body, messaging_config: MessagingConfig
    ) -> MessageProviderBase:
        """Returns correct messaging service based on the request body"""
        if "payload" in request_body:
            return BirdSMSProvider.from_config(messaging_config.BIRD)
        elif "update_id" in request_body:
            return Telegram.from_config(messaging_config.TELEGRAM)
        else:
            raise NotImplementedError("Messaging platform not implemented yet.")

    def _get_user_and_agent_from_db(self, message: ZootopiaMessage) -> Tuple[UserTableModel, AgentTableModel]:
        """Returns user object from database using message metadata"""
        user = None
        agent = None

        # Get user
        if message.provider == MessageProvider.TELEGRAM:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__telegram_uid.value: message.metadata.uid}
            )
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={Tables.AGENTS__telegram_chat_id.value: message.metadata.chat_id}

            )
        elif message.provider == MessageProvider.BIRD:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__phone_number.value: message.metadata.phone_number}
            )
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={Tables.AGENTS__bird_channel_id.value: message.metadata.channel_id}
            )
        
        # If no user exists, create user
        if not user:
            new_user = UserTableModel(
                telegram_uid=(
                    message.metadata.uid
                    if isinstance(message.metadata, TelegramMetadata)
                    else None
                ),
                phone_number=(
                    message.metadata.phone_number
                    if isinstance(message.metadata, BirdMetadata)
                    else None
                ),
            )

            user = self.database.insert(Tables.USERS.value, new_user)

        if not agent:
            raise AgentNotFoundError(f"Couldn't retrieve agent. Make sure the agent row matches incoming metadata: {message.metadata}")
        
        return user, agent
    
    def _get_or_create_room_from_db(
       self, user: UserTableModel, agent: AgentTableModel
    ) -> RoomTableModel:
        logger.info(agent)

        """Returns room object from database using message metadata"""
        room = self.database.get_row(
            Tables.ROOMS.value,
            conditions={
                Tables.ROOMS__user_id.value: user.id,
                Tables.ROOMS__agent_id.value: agent.id
            }
        )

        if not room:
            room = RoomTableModel(user_id=user.id, agent_id=agent.id)
            user = self.database.insert(Tables.ROOMS.value, room)

        return room
