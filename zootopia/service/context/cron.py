from zootopia.service.context.base import ContextService
from zootopia.core.schema import Tables
from zootopia.manager.messaging import BirdManager


class CronContextService(ContextService):
    @classmethod
    async def create(cls, room_id: int):
        context = cls()
        context.messaging_manager = BirdManager()
        context.room = await context.database_manager.get_row(
            Tables.ROOMS.value, conditions={Tables.ROOMS__id.value: room_id}
        )
        context.user = await context.database_manager.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__id.value: context.room.user_id},
        )
        context.agent = await context.database_manager.get_row(
            Tables.AGENTS.value,
            conditions={Tables.AGENTS__id.value: context.room.agent_id},
        )
        context.messaging_manager.set_channel_id(context.agent.bird_channel_id)
        context.messaging_manager.set_user_phone(context.user.phone_number)
        return context
