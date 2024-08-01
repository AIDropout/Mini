from zootopia.core.schema import (
    RoomTableModel,
    MessageTableModel,
)
from zootopia.controller.tasks.tasks import Task, RespondTask, ReviveTask, RemindTask

from zootopia.services import MessageProvider
from zootopia.database import SupabaseDB

from zootopia.core.exceptions import RequestCanceledException
from zootopia.controller.context import BaseContextManager
from zootopia.controller.agent.filter import MessageFilter, FilterInput
from zootopia.controller.agent.action import ActionManager
from zootopia.controller.agent.memory import MemoryManager

from zootopia.core.logger import logger
from zootopia.core.utils.utils import get_current_time_readable


class Agent:
    def __init__(
        self,
        messaging_service: MessageProvider,
        database_service: SupabaseDB,
        room: RoomTableModel,
        agent_prompt: str,
    ) -> None:
        self.agent_prompt = agent_prompt
        self.room = room
        self.database_service = database_service
        self.filter = MessageFilter()
        self.action = ActionManager(messaging_service)
        self.memory = MemoryManager(database_service, room)

    @classmethod
    def from_context(cls, context: BaseContextManager) -> "Agent":
        return cls(
            messaging_service=context.messaging_service,
            database_service=context.database,
            room=context.room,
            agent_prompt=context.agent.prompt,
        )

    async def handle_chat_task(self, task: Task) -> bool:
        logger.info(f"🟢 {task}")

        try:
            # Get recent messages
            recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )

            # If responding to user, store user message
            if isinstance(task, RespondTask):
                msg = task.user_message.content

                self.memory.store_message(
                    MessageTableModel(
                        room_id=self.room.id,
                        from_user=True,
                        content=msg,
                    )
                )

                # Save event to schedules table and add it to Redis scheduler
                # self.action.detect_intent(text=msg)

                recent_messages.append(
                    {"role": "user", "content": msg}
                )

            system_prompt_template = """
            {agent_prompt}

            Your task: {instructions}

            It is now {current_time}
            {prompt_addition}

            You can send multiple messages by separating messages by a pipe symbol. Only if needed
            """

            # A separate LLM checks to see if LLM response meets criteria
            max_attempts = 2
            prompt_addition = ""

            for attempt in range(max_attempts):

                system_prompt = system_prompt_template.format(
                    agent_prompt=self.agent_prompt,
                    instructions=task.instructions,
                    current_time=get_current_time_readable(),
                    prompt_addition=prompt_addition,
                )

                logger.info(
                    f"🟢 System prompt (Attempt {attempt + 1}/{max_attempts}):\n{system_prompt}"
                )
                logger.info(f"🟢 Recent messages:\n{recent_messages}")

                response_text = self.action.generate_message(
                    recent_messages, system_prompt
                )

                filter_result = self.filter.verify(
                    FilterInput(
                        from_user=False,
                        agent_prompt=self.agent_prompt,
                        messages=recent_messages,
                        new_message=response_text,
                    )
                )

                logger.info(filter_result.message)

                # If approved by filter, continue sending and storing
                if filter_result.approved:
                    await self.action.handle_message_send(response_text)
                    self.memory.store_message(
                        MessageTableModel(
                            room_id=self.room.id, from_user=False, content=response_text
                        )
                    )
                    return True

                if attempt == max_attempts - 1:
                    logger.warning(
                        f"Max attempts ({max_attempts}) reached. Unable to generate appropriate response."
                    )
                    return False

                # Prepare for next iteration if not approved
                prompt_addition = filter_result.prompt_addition

            return False

        except RequestCanceledException:
            logger.info(f"Request cancelled for room {self.room.id} due to new request")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in processing chat: {str(e)}")
            return False
