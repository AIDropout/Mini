"""Class used to store utils needed for agent_controller logic"""

from config.config import Config, SupabaseConfig, MessagingConfig
from zootopia.core.schema import Tables, AgentTableModel, RoomTableModel, UserTableModel
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.platform.platform import MessageProviderBase
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.platform.models import (
    BirdMetadata,
    MessageProvider,
    TelegramMetadata,
    ZootopiaMessage,
)
from zootopia.platform.telegram.telegram import Telegram

def get_or_create_room_from_db(
       user: UserTableModel, agent: AgentTableModel, database: SupabaseDB
    ) -> RoomTableModel:
        """Returns room object from database using message metadata. This function is also used by signup"""
        room = database.get_row(
            Tables.ROOMS.value,
            conditions={
                Tables.ROOMS__user_id.value: user.id,
                Tables.ROOMS__agent_id.value: agent.id
            }
        )

        if not room:
            room = RoomTableModel(user_id=user.id, agent_id=agent.id)
            user = database.insert(Tables.ROOMS.value, room)
        return room

class ContextManager:
    def __init__(self, request_body, supabase_config: SupabaseConfig, messaging_config: MessagingConfig):
        """
        1. Init database
        2. Init correct messaging service given the message
        3. Use messaging service to format it into a ZootopiaMessage object
        4. Use ZootopiaMessage to locate correct user, room & store in ZootopiaAppState variables
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
        self.user: UserTableModel = self._get_or_create_user_from_db(self.message)
        self.agent: AgentTableModel = self._get_or_create_agent_from_db(self.message)
        self.room: RoomTableModel = get_or_create_room_from_db(
            self.user, self.agent, database=self.database
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

    def _get_or_create_user_from_db(self, message: ZootopiaMessage) -> UserTableModel:
        """Returns user object from database using message metadata"""
        user = None

        # Get user
        if message.provider == MessageProvider.TELEGRAM:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__telegram_uid.value: message.metadata.uid}
            )
        elif message.provider == MessageProvider.BIRD:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__phone_number.value: message.metadata.phone_number}
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

        return user

    def _get_or_create_agent_from_db(self, message: ZootopiaMessage) -> AgentTableModel:
        """Returns agent object from database using message metadata"""
        agent = None

        # Get agent
        if message.provider == MessageProvider.TELEGRAM:
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={}  # Add appropriate conditions if needed
            )
        elif message.provider == MessageProvider.BIRD:
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={Tables.AGENTS__bird_channel_id.value: message.metadata.channel_id}
            )

        # If no agents exists, create one
        if not agent:
            new_agent = AgentTableModel(
                telegram_chat_id=(
                    message.metadata.chat_id
                    if isinstance(message.metadata, TelegramMetadata)
                    else None
                ),
                bird_channel_id=(
                    message.metadata.channel_id
                    if isinstance(message.metadata, BirdMetadata)
                    else None
                ),
            )

            agent = self.database.insert(Tables.AGENTS.value, new_agent)

        return agent
