from zootopia.service.context.base import ContextService
from zootopia.core.schema import (
    ZootopiaMessage,
    User,
    Agent,
    Room,
    Tables,
    MessageProvider,
)
from zootopia.core.exceptions import AgentNotFoundError


class MessageContextService(ContextService):
    def __init__(self, message: ZootopiaMessage):
        super().__init__()
        self.message = message
        self.user = None
        self.agent = None
        self.room = None

    @classmethod
    async def create(cls, message: ZootopiaMessage):
        context = cls(message)
        await context._initialize()
        return context

    async def _initialize(self):
        self.user, self.agent = await self._get_user_and_agent_from_db()
        self.room = await self._get_or_create_room()

    async def _get_user_and_agent_from_db(self):
        user = None
        agent = None

        if self.message.provider == MessageProvider.TELEGRAM:
            user = await self.database_manager.get_row(
                Tables.USERS.value,
                conditions={
                    Tables.USERS__telegram_uid.value: self.message.metadata.uid
                },
            )
            agent = await self.database_manager.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__telegram_chat_id.value: self.message.metadata.chat_id
                },
            )
        elif self.message.provider == MessageProvider.BIRD:
            user = await self.database_manager.get_row(
                Tables.USERS.value,
                conditions={
                    Tables.USERS__phone_number.value: self.message.metadata.phone_number
                },
            )
            agent = await self.database_manager.get_row(
                Tables.AGENTS.value,
                conditions={
                    Tables.AGENTS__bird_channel_id.value: self.message.metadata.channel_id
                },
            )

        if not user:
            user = await self._create_new_user()

        if not agent:
            raise AgentNotFoundError(
                f"Couldn't retrieve agent. Make sure the agent row matches incoming metadata: {self.message.metadata}"
            )

        return user, agent

    async def _create_new_user(self):
        new_user = User(
            telegram_uid=(
                self.message.metadata.uid
                if self.message.provider == MessageProvider.TELEGRAM
                else None
            ),
            phone_number=(
                self.message.metadata.phone_number
                if self.message.provider == MessageProvider.BIRD
                else None
            ),
        )
        return await self.database_manager.insert(Tables.USERS.value, new_user)

    async def _get_or_create_room(self):
        room = await self.database_manager.get_row(
            Tables.ROOMS.value,
            conditions={
                Tables.ROOMS__user_id.value: self.user.id,
                Tables.ROOMS__agent_id.value: self.agent.id,
            },
        )
        if not room:
            room = Room(user_id=self.user.id, agent_id=self.agent.id)
            room = await self.database_manager.insert(Tables.ROOMS.value, room)
        return room
