# from mini.core.logger import get_logger
# from mini.database.models import Message, Tables
# from mini.messaging.provider.bird.bird import BirdMessaging
# from mini.messaging.context import ContextFactory
# from mini.database.database import DatabaseManager

# logger = get_logger(__name__)


# # TODO: convert this to a celery task
# class DashboardService:
#     def __init__(
#         self,
#         database_manager: DatabaseManager,
#         context_factory: ContextFactory,
#     ):
#         self.database_manager = database_manager
#         self.context_factory = context_factory

#     def send_admin_message(self, room_id: str, message: str):

#         context = self.context_factory.get_context_from_room_id(room_id)

#         bird_manager = BirdMessaging()
#         bird_manager.set_receiver(context.user.phone_number)
#         bird_manager.set_sender(context.agent.bird_channel_id)
#         success = bird_manager.send_message(text=message)

#         if success:
#             new_message = Message(
#                 sender_id=context.room.agent_id,
#                 room_id=room_id,
#                 content=message,
#                 sent_by_admin=True,
#             )

#             self.database_manager.insert(Tables.MESSAGES, new_message)
