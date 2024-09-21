import json
from typing import Union

from config.config import config
from mini.agent.modules.action import ActionModule
from mini.agent.modules.filter.filter import MessageFilterModule
from mini.agent.modules.memory.service import MemoryModule
from mini.agent.modules.prompt import (
    AgentPromptModule,
    BasePromptModule,
    ChatMessage,
    RoleplayPromptModule,
)
from mini.agent.modules.subscribe import SubscribeModule
from mini.agent.modules.vision import VisionModule
from mini.agent.tasks.models import RespondTask
from mini.core.event_logger import event_logger as el
from mini.core.exceptions import VisionError
from mini.core.logger import get_logger
from mini.database.models import Agent, Message, Room, Tables, User
from mini.database.database import DatabaseManager
from mini.messaging.bird.bird import BirdManager
from mini.messaging.discord.discord import discord_manager
from mini.server.cancel import CancelManager
from mini.utils.utils import utc_now


class AgentService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        cancel_manager: CancelManager,
        action_module: ActionModule,
        memory_module: MemoryModule,
        subscribe_module: SubscribeModule,
        filter_module: MessageFilterModule,
        vision_module: VisionModule,
        prompt_module: BasePromptModule,
    ) -> None:
        self.database_manager = database_manager
        self.cancel_manager = cancel_manager
        self.logger = get_logger(__name__)
        self.agent: Agent = None
        self.user: User = None
        self.room: Room = None
        self.action = action_module
        self.memory = memory_module
        self.subscribe = subscribe_module
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

    def configure(
        self, messaging_manager: BirdManager, agent: Agent, user: User, room: Room
    ) -> None:
        self.agent, self.user, self.room = agent, user, room
        for module in [
            self.memory,
            self.filter,
            self.subscribe,
            self.action,
            self.vision,
            self.agent_prompt,
            self.roleplay_prompt,
        ]:
            module.configure(room, agent, user)
        self.action.set_messaging_manager(messaging_manager)

    def handle_chat_task(
        self, task: RespondTask
    ) -> bool:
        el.log(f"TASK: {task}")
        try:
            if isinstance(task, RespondTask):
                task = self._handle_respond_task(task)
                if not self._should_continue_conversation():
                    return True

            response, roleplay = self._generate_response(task)
            text_response = f"**{roleplay}**\n\n{response}" if roleplay else response

            if self._is_task_cancelled(task):
                return False

            success = self.action.send_message(text=text_response)
            el.log(f"BIRD SMS SENT: {success}")

            if success:
                self._handle_successful_send(text_response)

            return True
        except Exception:
            msg = discord_manager.log_error(f"task_id={task.id}")
            el.log(msg)
            return False

    def _handle_respond_task(self, task: RespondTask) -> RespondTask:
        if task.user_message.media_urls:
            task = self._handle_image(task)
        el.log(f"RESPONDING TO: '{task.user_message.content}' in Room {self.room.id}")
        return task

    def _should_continue_conversation(self) -> bool:
        result = self.subscribe.should_continue_conversation()
        self.logger.info(f"Room subscription status: {repr(result)}")
        return result.continue_conversation

    def _generate_response(
        self, task: RespondTask
    ) -> tuple[str, str]:
        all_recent_messages = self.memory.get_recent_messages(
            count=task.recent_message_count
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

            roleplay_response_text = self.action.generate_message(
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
        )
        el.log(f"SYSTEM PROMPT FOR AGENT: {agent_system_prompt}")

        agent_response_text = self.action.generate_message(
            [], agent_system_prompt, self.agent_prompt.response_format
        )
        el.log(f"AGENT LLM RESPONSE: {agent_response_text}")

        response = json.loads(agent_response_text).get("best_response", "")
        return (
            self.filter.validate_message(all_recent_messages, response),
            roleplay_response,
        )

    def _is_task_cancelled(
        self, task: RespondTask
    ) -> bool:
        return self.cancel_manager.newer_task_found(self.room.id, task.id)

    def _handle_image(self, task: RespondTask) -> RespondTask:
        try:
            description = self.vision.handle_images(task.user_message.media_urls)
            task.user_message.content += f"\n\nUser sent an image: {description}"
        except VisionError:
            task.user_message.content += (
                "\n\nUser sent an image, but due to some error your phone "
                "is not receiving images currently."
            )
        return task

    def _handle_successful_send(self, final_message: str):
        self._add_message_to_db(final_message)
        self._log_to_discord(final_message)
        self._update_room_last_message_time()

    def _add_message_to_db(self, final_message: str):
        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=self.room.id,
                sender_id=self.agent.id,
                content=final_message,
                log=el.get_logs(),
            ),
        )

    def _log_to_discord(self, final_message: str):
        if config.ENVIRONMENT == "production":
            discord_manager.log_message(
                message=f"-# {self.agent.name} -> {self.user.phone_number}: {final_message}",
            )

    def _update_room_last_message_time(self):
        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__agent_last_msg_sent_at: utc_now()},
            condition_key=Tables.ROOMS__id,
            condition_value=self.room.id,
        )
