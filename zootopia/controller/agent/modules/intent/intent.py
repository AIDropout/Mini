# from zootopia.controller.agent.modules.base import AgentModule
# from zootopia.manager.database import DatabaseManager
# from zootopia.core.schema.tables import Tables
# from zootopia.controller.agent.modules.intent.schedule import ScheduleIntentInput
# from zootopia.core.schema.intent import IntentType
# from zootopia.controller.agent.modules.intent import IntentConfig
# from zootopia.core.logger import logger
# from typing import Dict


# class IntentModule(AgentModule):
#     def __init__(
#         self,
#         database_manager: DatabaseManager,
#         filter_intent,
#         skip_intent,
#         schedule_intent,

#     ):
#         self.database_manager = database_manager
#         self.filter_intent = filter_intent
#         self.skip_intent = skip_intent
#         self.schedule_intent = schedule_intent

#     def process_filter_intent(self, response_text: str):
#                         # Use Filter intent to ensure quality of agent response
#         filter_result = None
#         if not self.intent_config.is_enabled(IntentType.FILTER):
#             filter_result = FilterIntentResult(
#                 from_user=False,
#                 analyzed_message=response_text,
#                 approved=True,
#                 confidence=Confidence.HIGH,
#                 proposed_message="",
#             )
#         else:
#             filter_intent = self.intent_factory.create(IntentType.FILTER)
#             if filter_intent:
#                 filter_messages = self.intent_config.get_past_messages(
#                     IntentType.FILTER, all_recent_messages
#                 )
#                 filter_result: FilterIntentResult = filter_intent.process(
#                     input=FilterIntentInput(
#                         from_user=False,
#                         agent_prompt=self.agent.prompt,
#                         messages=filter_messages,
#                         message=response_text,
#                     ),
#                     confidence_threshold=self.intent_config.get_confidence_threshold(
#                         IntentType.FILTER
#                     ),
#                 )

#         el.log(f"{filter_result.message}")

#         # If approved by filter or if there's a high-confidence proposed message, send and store
#         if filter_result.approved:
#             return response_text
#         elif filter_result.proposed_message:
#             return filter_result.proposed_message
#         else:
#             return False

#     def process_schedule_intent(
#         self, user_message: str
#     ) -> Optional[Schedule]:
#         if not self.schedule_intent.is_enabled:
#             return None

#         existing_tasks = self.database_manager.get_multiple_rows(
#             table_name=Tables.SCHEDULE,
#             conditions={Tables.SCHEDULE__room_id: self.room.id},
#             order_by=Tables.SCHEDULE__run_at,
#             order_details=False,
#         )

#         logger.info(f"Existing scheduled tasks for room {self.room.id}: {existing_tasks}")

#         schedule_result = self.schedule_intent.process(
#             input=ScheduleIntentInput(
#                 message=user_message, existing_tasks=existing_tasks
#             ),
#             confidence_threshold=self.intent_config.get_confidence_threshold(
#                 "SCHEDULE"
#             ),
#         )

#         if schedule_result.approved:
#             inserted_task = self.database_manager.insert(
#                 table_name=Tables.SCHEDULE,
#                 item=Schedule(
#                     room_id=self.room.id,
#                     run_at=schedule_result.run_at,
#                     type=TaskType.REMIND,
#                     task=schedule_result.task,
#                     complete=False,
#                 ),
#             )

#             logger.info(f"Scheduled a task: {inserted_task}")
#             return inserted_task

#         return None
