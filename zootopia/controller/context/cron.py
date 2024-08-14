from zootopia.service import BirdSMSProvider
from zootopia.core.schema import Tables
from zootopia.controller.context import BaseContextManager


class CronContextManager(BaseContextManager):
    def __init__(self, room_id):
        super().__init__()
        self.messaging_service = BirdSMSProvider()
        self.room = self.database.get_row(
            Tables.ROOMS.value, conditions={Tables.ROOMS__id.value: room_id}
        )
        self.user = self.database.get_row(
            Tables.USERS.value, conditions={Tables.USERS__id.value: self.room.user_id}
        )
        self.agent = self.database.get_row(
            Tables.AGENTS.value,
            conditions={Tables.AGENTS__id.value: self.room.agent_id},
        )
        self.messaging_service.set_channel_id(self.agent.bird_channel_id)
        self.messaging_service.set_user_phone(self.user.phone_number)
