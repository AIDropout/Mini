from datetime import datetime
from typing import Union

from langchain_core.messages import HumanMessage

from zootopia.controller.action.autodb.autodb import AutoDB
from config.config import autodb_config, config
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.core.schema.llm import ImitateChat, LLMConfig, LLMNames, LLMProviders
from zootopia.messaging.messaging  import MessageProviderBase
from zootopia.messaging.models import ZootopiaMessage
from zootopia.core.logger import logger
from zootopia.core.utils.utils import render_jinja_template


class CommunicateManager:
    def __init__(
        self,
        messaging_service: MessageProviderBase,
        message: ZootopiaMessage,
        database: SupabaseDB,
    ) -> None:
        self.messaging_service = messaging_service
        self.database = database
        self.message = message
        self.relevant_user_data = None
        self.chat = []

    def get_relevant_user_data(self):
        autodb = AutoDB.from_config(autodb_config)
        data = autodb.get_data(self.message.message.message.text, self.database)
        self.relevant_user_data = data
        logger.info(data)

    def get_past_conversation(self):
        messages = self.database.get_rows(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE
        )[0][1]

        if len(messages) > 0:
            self.chat.extend(
                LLM.imitate_chat(
                    [
                        ImitateChat(
                            message=message["message"], is_llm=message["from_bot"]
                        )
                        for message in messages
                    ]
                )
            )

    async def send_llm_response_message(self):
        system_prompt = render_jinja_template(
            "respond.jinja",
            "zootopia/manager/communicate/templates",
            username=self.message.user_name,
            time=datetime.now().isoformat(),
            user_information=self.relevant_user_data,
        )

        llm_config = LLMConfig(provider=LLMProviders.GOOGLE, name=LLMNames.GEMINI_PRO)
        llm = LLM(llm_config)

        llm.system_prompt = system_prompt
        response = llm.generate_response(
            self.chat + [HumanMessage(content=self.message.message.message.text)]
        ).content

        self.database.insert(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE,
            {"id": self.database.user_id, "from_bot": True, "message": response},
        )
        return await self.messaging_service.send_message(response)
