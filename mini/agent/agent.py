import json
from typing import Union

from config.config import config
from mini.agent.modules.sender import MessageSenderModule
from mini.agent.modules.filter.filter import MessageFilterModule
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.proactive.schedule_dispatch import ScheduleDispatch
from mini.agent.modules.prompt import (
    AgentPromptModule,
    BasePromptModule,
    ChatMessage,
    RoleplayPromptModule,
)
from mini.agent.modules.subscribe import SubscribeModule
from mini.agent.modules.vision import VisionModule
from mini.core.event_logger import event_logger as el
from mini.core.exceptions import VisionError
from mini.core.logger import get_logger
from mini.core.models.message import MiniMessage
from mini.messaging.tasks.models import ProactiveTask, ResponseTask
from mini.database.database import DatabaseManager
from mini.database.models import Agent, Room, User
from mini.messaging.providers.discord import discord_manager
from mini.server.redis.cancel import CancelManager


class AgentService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        schedule_dispatch: ScheduleDispatch,
        cancel_manager: CancelManager,
        message_sender_module: MessageSenderModule,
        memory_module: MemoryModule,
        subscribe_module: SubscribeModule,
        filter_module: MessageFilterModule,
        vision_module: VisionModule,
        prompt_module: BasePromptModule,
    ) -> None:
        self.database_manager = database_manager
        self.cancel_manager = cancel_manager
        self.schedule_dispatch = schedule_dispatch
        self.logger = get_logger(__name__)
        self.agent: Agent = None
        self.user: User = None
        self.room: Room = None
        self.message_sender = message_sender_module
        self.memory = memory_module
        self.subscribe = subscribe_module  # TODO: move this outside agent
        self.filter = filter_module
        self.vision = vision_module
        self.agent_prompt = AgentPromptModule(
            database_manager=prompt_module.database_manager,
            time_manager=prompt_module.time_manager,
        )
        self.roleplay_prompt = RoleplayPromptModule(
            database_manager=prompt_module.database_manager,
            time_manager=prompt_module.time_manager,
        )

    def _configure(
        self,
        agent: Agent,
        user: User,
        room: Room,
    ) -> None:
        self.agent, self.user, self.room = agent, user, room
        for module in [
            self.memory,
            self.filter,
            self.subscribe,
            self.message_sender,
            self.vision,
            self.agent_prompt,
            self.roleplay_prompt,
            self.schedule_dispatch,
        ]:
            module.configure(room, agent, user)

    def process_chat_task(
        self,
        task: Union[ResponseTask, ProactiveTask],
    ) -> bool:
        """Processes a chat task and removes it from queue"""
        # Configure modules
        self._configure(task.context.agent, task.context.user, task.context.room)
        self.message_sender.set_messaging_provider(task.messaging_provider)

        # Handle each task type
        if isinstance(task, ResponseTask):
            result = self._handle_response_task(task)
        elif isinstance(task, ProactiveTask):
            result = self._handle_proactive_task(task)

        self._update_proactive_message_schedule()

        # Remove task
        # self.cancel_manager.remove_task(task.context.room.id, task.id)

        return result

    def _handle_proactive_task(self, task: ProactiveTask) -> bool:
        el.log("BUILDING PROACTIVE MESSAGE...")
        try:
            response, roleplay = self._generate_response(
                message=None, is_proactive=True
            )

            text_response = f"**{roleplay}**\n\n{response}" if roleplay else response

            return self.message_sender.send_message(text=text_response)
        except Exception as e:
            msg = discord_manager.log_error(str(e))
            el.log(msg)
            return False

    def _handle_response_task(self, task: ResponseTask) -> bool:
        el.log(f"MESSAGE: {task.message.content}")
        try:
            if task.message.media_urls:
                task = self._handle_image(task.message)
                el.log(
                    f"RESPONDING TO: '{task.message.content}' in Room {self.room.id}"
                )

            # TODO: move this to admin service
            if (
                not self._should_continue_conversation()
            ):  
                return True

            response, roleplay = self._generate_response(task.message)
            
            text_response = f"**{roleplay}**\n\n{response}" if roleplay else response

            return self.message_sender.send_message(text=text_response)

        except Exception:
            msg = discord_manager.log_error(f"task_id={task.id}")
            el.log(msg)
            return False

    def _should_continue_conversation(self) -> bool:
        result = self.subscribe.should_continue_conversation()
        self.logger.info(f"Room subscription status: {repr(result)}")
        return result.continue_conversation

    def _generate_response(
        self, message: MiniMessage | None, is_proactive: bool = False
    ) -> tuple[str, str]:
        all_recent_messages = self.memory.get_recent_messages(
            count=10  # TODO: Make this configurable?
        )
        el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

        chat_history = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in all_recent_messages
        ]

        # ROLEPLAY MESSAGE
        roleplay_response = ""
        if self.agent.allow_roleplay:
            roleplay_system_prompt = self.roleplay_prompt.build_prompt(
                relevant_memories="", chat_history=chat_history
            )
            el.log(f"SYSTEM PROMPT FOR ROLEPLAY: {roleplay_system_prompt}")

            roleplay_response_text = self.message_sender.generate_message(
                [], roleplay_system_prompt, self.roleplay_prompt.response_format
            )
            el.log(f"ROLEPLAY LLM RESPONSE: {roleplay_response_text}")
            roleplay_response = json.loads(roleplay_response_text).get(
                "best_response", ""
            )

        # AGENT MESSAGE
        agent_system_prompt = self.agent_prompt.build_prompt(
            relevant_memories="",
            chat_history=chat_history,
            roleplay=roleplay_response,
            proactive_prompt=is_proactive,
        )
        el.log(f"SYSTEM PROMPT FOR AGENT: {agent_system_prompt}")

        agent_response_text = self.message_sender.generate_message(
            [], agent_system_prompt, self.agent_prompt.response_format
        )
        el.log(f"AGENT LLM RESPONSE: {agent_response_text}")

        response = json.loads(agent_response_text).get("best_response", "")
        return (
            self.filter.validate_message(all_recent_messages, response),
            roleplay_response,
        )

    def _handle_image(self, message: MiniMessage) -> ResponseTask:
        try:
            description = self.vision.handle_images(message.media_urls)
            message.content += f"\n\nUser sent an image: {description}"
        except VisionError:
            message.content += (
                "\n\nUser sent an image, but due to some error your phone "
                "is not loading the images."
            )
        return message

    def _update_proactive_message_schedule(self):
        self.schedule_dispatch.schedule_proactive_message()
