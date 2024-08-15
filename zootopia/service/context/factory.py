from zootopia.service.context.message import MessageContextService
from zootopia.service.context.cron import CronContextService
from zootopia.manager.messaging.factory import MessagingManagerFactory


class ContextFactory:
    def __init__(self, messaging_manager_factory: MessagingManagerFactory):
        self.messaging_manager_factory = messaging_manager_factory

    def create_message_context(self, request_body: dict) -> MessageContextService:
        """Takes a request body and creates the proper context"""
        messaging_manager = self.messaging_manager_factory.get_manager_from_request(
            request_body
        )
        message = messaging_manager.receive_message(request_body)
        return MessageContextService.create(message)

    def create_cron_context(self, room_id: int) -> CronContextService:
        return CronContextService.create(room_id)
