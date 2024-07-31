from zootopia.services import BirdSMSProvider, Telegram
from typing import Union
from zootopia.core.schema import (
    ZootopiaMessage,
    MessageProvider,
    Tables,
    UserTableModel,
    TaskType,
)
from zootopia.core.exceptions import AgentNotFoundError
from zootopia.controller.context import BaseContextManager


class MessageContextManager(BaseContextManager):
    """THis class differs in that it also holds a message variable for the agent to reference"""

    def __init__(self, request_body: dict):
        super().__init__()
        self.messaging_service = self.get_messaging_service(request_body)
        self.message: ZootopiaMessage = self.messaging_service.receive_message(
            request_body
        )
        self.user, self.agent = self._get_user_and_agent_from_db(self.message)
        self.room = self._get_or_create_room(self.user, self.agent)

    def get_messaging_service(
        self, request_body: dict
    ) -> Union[BirdSMSProvider, Telegram]:
        if "payload" in request_body:
            return BirdSMSProvider()
        elif "update_id" in request_body:
            return Telegram()
        else:
            raise NotImplementedError("Messaging platform not implemented yet.")

    def _get_user_and_agent_from_db(self, message: ZootopiaMessage):
        user = None
        agent = None

        if message.provider == MessageProvider.TELEGRAM:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={Tables.USERS__telegram_uid.value: message.metadata.uid},
            )
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__telegram_chat_id.value: message.metadata.chat_id
                },
            )
        elif message.provider == MessageProvider.BIRD:
            user = self.database.get_row(
                Tables.USERS.value,
                conditions={
                    Tables.USERS__phone_number.value: message.metadata.phone_number
                },
            )
            agent = self.database.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__bird_channel_id.value: message.metadata.channel_id
                },
            )

        if not user:
            user = self._create_new_user(message)

        if not agent:
            raise AgentNotFoundError(
                f"Couldn't retrieve agent. Make sure the agent row matches incoming metadata: {message.metadata}"
            )

        return user, agent

    def _create_new_user(self, message: ZootopiaMessage):
        new_user = UserTableModel(
            telegram_uid=(
                message.metadata.uid
                if message.provider == MessageProvider.TELEGRAM
                else None
            ),
            phone_number=(
                message.metadata.phone_number
                if message.provider == MessageProvider.BIRD
                else None
            ),
        )
        return self.database.insert(Tables.USERS.value, new_user)
