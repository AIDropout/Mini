from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.schema import Tables
from zootopia.context import BaseContextManager
from config.config import Config

class CronContextManager(BaseContextManager):
    def __init__(self, config: Config, agent_id, user_id, room_id):
        super().__init__(config)
        self.messaging_service = BirdSMSProvider.from_config(self.config.MESSAGING_CONFIG.BIRD)
        self.user = self.database.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__id.value: user_id}
        )
        self.agent = self.database.get_row(
            Tables.AGENTS.value,
            conditions={Tables.AGENTS__id.value: agent_id}
        )
        self.room = self.database.get_row(
            Tables.ROOMS.value,
            conditions={Tables.ROOMS__id.value: room_id}
        )
        self.messaging_service.set_channel_id(self.agent.bird_channel_id)
        self.messaging_service.set_user_phone(self.user.phone_number)