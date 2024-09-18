import json
from typing import Union

from config.config import config
from mini.controller.agent.modules.action import ActionModule
from mini.controller.agent.modules.intent.filter import FilterModule
from mini.controller.agent.modules.memory import MemoryModule
from mini.controller.agent.modules.prompt import PromptModule
from mini.controller.agent.modules.subscribe import SubscribeModule
from mini.controller.agent.modules.vision import VisionModule
from mini.controller.task.task_types import RemindTask, RespondTask, ReviveTask
from mini.core.event_logger import event_logger as el
from mini.core.exceptions import VisionError
from mini.core.logger import get_logger
from mini.core.schema.tables import Agent, Message, Room, Tables, User
from mini.manager.database import DatabaseManager
from mini.manager.messaging import MessagingManager, discord_manager
from mini.server.cancel import CancelManager
from mini.service.base import Service
from mini.utils.utils import log_error_to_discord, utc_now


class AgentService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        cancel_manager: CancelManager,
        action_module: ActionModule,
        memory_module: MemoryModule,
        subscribe_module: SubscribeModule,
        filter_module: FilterModule,
        vision_module: VisionModule,
        prompt_module: PromptModule,
    ) -> None:
        super().__init__(database_manager)
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
        self.prompt = prompt_module

    def configure(
        self, messaging_manager: MessagingManager, agent: Agent, user: User, room: Room
    ) -> None:
        self.agent, self.user, self.room = agent, user, room
        for module in [
            self.memory,
            self.filter,
            self.subscribe,
            self.action,
            self.vision,
            self.prompt,
        ]:
            module.configure(room, agent, user)
        self.action.set_messaging_manager(messaging_manager)

    def handle_chat_task(
        self, task: Union[RespondTask, RemindTask, ReviveTask]
    ) -> bool:
        el.log(f"TASK: {task}")
        try:
            if isinstance(task, RespondTask):
                task = self._handle_respond_task(task)
                if not self._should_continue_conversation():
                    return True

            response = self._generate_response(task)
            if self._is_task_cancelled(task):
                return False

            success = self.action.send_message(text=response)
            el.log(f"BIRD SMS SENT: {success}")

            if success:
                self._handle_successful_send(task.type, response)

            return True
        except Exception:
            msg = log_error_to_discord("task_id", task.id)
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
        self, task: Union[RespondTask, RemindTask, ReviveTask]
    ) -> str:
        all_recent_messages = self.memory.get_recent_messages(
            count=task.recent_message_count
        )
        el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

        system_prompt = self.prompt.build_prompt(
            relevant_memories="", chat_history=all_recent_messages
        )
        el.log(f"SYSTEM PROMPT FOR AGENT: {system_prompt}")

        response_text = self.action.generate_message(
            [], system_prompt, self.prompt.response_format
        )
        el.log(f"MAIN LLM RESPONSE: {response_text}")

        response = json.loads(response_text).get("best_response", "")
        return self.filter.process_message(all_recent_messages, response)

    def _is_task_cancelled(
        self, task: Union[RespondTask, RemindTask, ReviveTask]
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

    def _handle_successful_send(self, task_type: str, final_message: str):
        self._add_message_to_db(task_type, final_message)
        self._log_to_discord(final_message)
        self._update_room_last_message_time()

    def _add_message_to_db(self, task_type: str, final_message: str):
        self.database_manager.insert(
            Tables.MESSAGES,
            Message(
                room_id=self.room.id,
                sender_id=self.agent.id,
                content=final_message,
                type=task_type,
                log=el.get_logs(),
            ),
        )

    def _log_to_discord(self, final_message: str):
        if config.ENVIRONMENT == "production":
            discord_manager.send_message_to_channel(
                message=f"-# {self.agent.name} -> {self.user.phone_number}: {final_message}",
                channel="https://discord.com/api/webhooks/1285123477619081237/xCmCDv_j0XV7Sm0xSAfbLxM603AaJML9TJVefhmiDkglfAmYwh9ElqYQgo88qHk1Ubz1",
            )

    def _update_room_last_message_time(self):
        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__agent_last_msg_sent_at: utc_now()},
            condition_key=Tables.ROOMS__id,
            condition_value=self.room.id,
        )
