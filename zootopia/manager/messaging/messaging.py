from typing import Union
from zootopia.core.schema import ZootopiaMessage, MessageProvider
from zootopia.manager.messaging import BirdManager, TelegramManager
from zootopia.service.context.message import MessageContextService
from zootopia.service.context.cron import CronContextService


class MessagingManager:
    def __init__(self):
        self.bird_manager = BirdManager()
        self.telegram_manager = TelegramManager()

    def get_messaging_manager(
        self, request_body: dict
    ) -> Union[BirdManager, TelegramManager]:
        if "payload" in request_body:
            return self.bird_manager
        elif "update_id" in request_body:
            return self.telegram_manager
        else:
            return self.bird_manager

    async def create_message_context(self, request_body: dict) -> MessageContextService:
        messaging_manager = self.get_messaging_manager(request_body)
        message = await messaging_manager.receive_message(request_body)
        return await MessageContextService.create(message)

    async def create_cron_context(self, room_id: int) -> CronContextService:
        return await CronContextService.create(room_id)
