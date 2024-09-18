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
from mini.core.schema.llm import LLMProviders
from mini.core.schema.tables import Agent, Message, Room, Tables, User
from mini.manager.database import DatabaseManager
from mini.manager.llm import LLMManager
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
        """Sets room details for the agent and its modules"""

        self.agent = agent
        self.user = user
        self.room = room
        self.memory.configure(room, agent, user)
        self.filter.configure(room, agent, user)
        self.subscribe.configure(room, agent, user)
        self.action.configure(room, agent, user)
        self.vision.configure(room, agent, user)
        self.prompt.configure(room, agent, user)
        self.action.set_messaging_manager(messaging_manager)

    def handle_chat_task(
        self, task: Union[RespondTask, RemindTask, ReviveTask]
    ) -> bool:
        """Core logic for generates and sending message"""

        el.log(f"TASK: {task}")

        try:
            if isinstance(task, RespondTask):
                # (The user's message has already been stored to db.)
                if len(task.user_message.media_urls) > 0:
                    task = self._handle_image(task)

                el.log(
                    f"RESPONDING TO: '{task.user_message.content}' in Room {self.room.id}"
                )

                result = self.subscribe.should_continue_conversation()
                self.logger.info(f"Room subscription status: {repr(result)}")

                if not result.continue_conversation:
                    return True

            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )
            el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

            relevant_memories = self.memory.get_relevant_memories(all_recent_messages)
            relevant_memories = "\n\n".join(relevant_memories)
            el.log(f"RELEVANT MEMORIES FOR CONVERSATION: {relevant_memories}")

            system_prompt = self.prompt.build_prompt(
                relevant_memories=relevant_memories, chat_history=all_recent_messages
            )
            el.log(f"SYSTEM PROMPT FOR AGENT: {system_prompt}")

            if self.cancel_manager.newer_task_found(self.room.id, task.id):
                return False
            response_text = self.action.generate_message([], system_prompt)
            el.log(f"MAIN LLM RESPONSE: {response_text}")

            response = json.loads(response_text).get("best_response", "")

            if self.cancel_manager.newer_task_found(self.room.id, task.id):
                return False

            final_message = self.filter.process_message(all_recent_messages, response)

            # TODO: fetch agent data and pass in this module before this function is run (would require a large-ish refactor)
            # Disabling this feature for now
            url = None
            content_type = None
            if False:
                self.tts_llm = LLMManager(
                    llm_name="openai/tts-1-hd", llm_provider=LLMProviders.OPENAI
                )
                url, content_type = self.tts_llm.generate_and_upload_speech(
                    text=final_message, voice="onyx"
                )

            if self.cancel_manager.newer_task_found(self.room.id, task.id):
                return False

            success = self.action.send_message(
                text=final_message, files=[(url, content_type)] if url else None
            )
            el.log(f"BIRD SMS SENT: {success}")

            if success:
                self._handle_successful_send(task.type, final_message)

            recent_message_count = task.recent_message_count * 2
            save_interval = recent_message_count  # this means every X'th message, memory saving will be triggered
            self.memory.save_relevant_memories(save_interval=save_interval)

        except Exception as e:
            msg = log_error_to_discord("task_id", task.id)
            el.log(msg)
            res = self.backup_handle_chat_task(task, str(e))
            return False

    def backup_handle_chat_task(
        self, task: Union[RespondTask, RemindTask, ReviveTask], error_message
    ) -> bool:
        """A watered-down verison of regular handle_chat_task, less error prone"""
        # TODO: after better exception handeling, tackle each exception differently
        # currently assuming user message has been saved to db
        el.log(f"TASK: {task}")
        el.log("🚨 WARNING: USING BACKUP METHOD, MEANS SOMETHING HAS FAILED 🚨")
        el.log(f"🚨 ERROR: {error_message}")
        el.log(f"RESPONDING TO: '{task.user_message.content}' in Room {self.room.id}")
        try:
            all_recent_messages = self.memory.get_recent_messages(
                count=task.recent_message_count
            )
            el.log(f"RECENT MESSAGES PASSED TO AGENT: {all_recent_messages}")

            system_prompt = self.prompt.build_prompt(
                relevant_memories="", chat_history=all_recent_messages
            )
            el.log(f"SYSTEM PROMPT FOR AGENT: {system_prompt}")

            response_text = self.action.generate_message([], system_prompt)
            el.log(f"MAIN LLM RESPONSE: {response_text}")
            response = json.loads(response_text).get("best_response")

            final_message = self.filter.process_message(all_recent_messages, response)

            success = self.action.send_message(final_message)
            el.log(f"BIRD SMS SENT: {success}")

            if success:
                self._handle_successful_send(task.type, final_message)
        except Exception as e:
            msg = log_error_to_discord("task_id", task.id)
            el.log(msg)
            return False

    def _handle_image(self, task: RespondTask) -> RespondTask:
        try:
            description = self.vision.handle_images(task.user_message.media_urls)
            task.user_message.content += f"\n\nUser sent an image: {description}"
        except VisionError:
            task.user_message.content += (
                "\n\nUser sent an image, but due to some error your phone "
                "is not recieving images currently."
            )

        return task

    def _construct_system_prompt(
        self, instructions: str, relevant_memories: str
    ) -> str:
        return f"""
        {self.agent.prompt}

        Your task: {instructions}

        - Carefully consider the context of recent messages to:
        a) Avoid repeating information already provided.
        b) Identify opportunities to drive the conversation forward, keeping it fresh and lively.

        Context:
        - time
        {self.memory.memory_manager.time_manager.current_readable_time()}

        - here are relevant memories:
        {relevant_memories}
        """

    def _handle_successful_send(self, task_type: str, final_message: str):
        """Adds agent message to DB & updates Rooms table"""
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

        # Log agent message to discord
        if config.ENVIRONMENT == "production":
            discord_manager.send_message_to_channel(
                message=f"-# {self.agent.name} -> {self.user.phone_number}: {final_message}",
                channel="https://discord.com/api/webhooks/1285123477619081237/xCmCDv_j0XV7Sm0xSAfbLxM603AaJML9TJVefhmiDkglfAmYwh9ElqYQgo88qHk1Ubz1",
            )

        self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__agent_last_msg_sent_at: utc_now()},
            condition_key=Tables.ROOMS__id,
            condition_value=self.room.id,
        )
