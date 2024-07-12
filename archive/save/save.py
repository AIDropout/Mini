from datetime import datetime, timedelta
from typing import Union

from tzlocal import get_localzone

from zootopia.controller.action.autodb.autodb import AutoDB
from config.config import autodb_config, config
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.apis.gsuite.gcal.gcal import GCal
from archive._intent import IntentManager
from zootopia.controller.intent.models import IntentFilters
from zootopia.core.schema.llm import LLMConfig, LLMNames, LLMProviders
from zootopia.messaging.messaging  import MessageProviderBase
from zootopia.messaging.models import ZootopiaMessage
from zootopia.core.logger import logger
from zootopia.core.utils.utils import render_jinja_template


class SaveManager:
    def __init__(
        self,
        messaging_service: MessageProviderBase,
        message: ZootopiaMessage,
        database: SupabaseDB,
    ) -> None:
        self.messaging_service = messaging_service
        self.database = database
        self.message = message
        self.creds = None
        self.saved_data = None
        self.saved_calendar_data = []

    def user_wants_to_save_data(self) -> bool:
        try:
            intent_filters = [
                IntentFilters(
                    title="question",
                    description=(
                        "based on the given data, the user has a question or wants to have a conversation"
                    ),
                ),
                IntentFilters(
                    title="inform",
                    description=(
                        "based on the given data, the user is logging, saving, "
                        "and/or tracking information"
                    ),
                ),
            ]
            llm_config = LLMConfig(
                provider=LLMProviders.GOOGLE, name=LLMNames.GEMINI_FLASH
            )
            llm = LLM(llm_config)
            intent_detector = IntentManager(llm, intent_filters)
            intent = intent_detector.detect_intent(self.message.message.message.text)
            logger.info(intent)

            if "INFORM" in intent:
                return True
        except Exception as e:
            logger.error("Unable to detect user's intent with message: %s", e)

        return False

    def _json_filter_formatter(self, json: dict) -> dict:
        json[config.DATABASE_CONFIG.CONSTANT_IDS.ID_COLUMN_NAME] = self.database.user_id
        return json

    def save_data_using_autodb(self):
        autodb = AutoDB.from_config(autodb_config)
        autodb.json_filter_formatter = self._json_filter_formatter
        text_message = self.message.message.message.text
        try:
            loc, act = autodb.save_data(text_message, self.database)
            self.saved_data = [(a.data, l.table) for a, l in zip(act, loc)]
            data_actions_str = ", ".join([str(a.data) for a in act])
            logger.info("saving the following to db: %s", data_actions_str)
            return True
        except Exception as e:
            logger.error("There was an error saving data using autodb: %s", e)
            return False

    def save_user_message_to_db(self):
        self.database.insert(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE,
            {
                "id": self.database.user_id,
                "from_bot": False,
                "message": self.message.message.message.text,
            },
        )

    def save_data_to_calendar(self):
        if self.saved_data is None:
            return

        gcal = GCal(self.creds)
        calendar_id = gcal.get_or_create_calendar(
            config.CALENDAR_CONFIG.CALENDAR_NAME,
            config.CALENDAR_CONFIG.CALENDAR_DESCRIPTION,
        )

        llm_config = LLMConfig(provider=LLMProviders.GOOGLE, name=LLMNames.GEMINI_FLASH)
        llm = LLM(llm_config)

        for data, location in self.saved_data:
            saved_data = f"{location}: {str(data)}"
            base_prompt = "You only give answers, no conversation, no extra fluff. "

            system_prompt = (
                "You will get some data, please generate a calendar title for it."
                "A related emoji must precede the title."
                "It must have the main action verb. It must be concise."
            )
            llm.system_prompt = base_prompt + system_prompt
            title = llm.generate_response(saved_data).content

            system_prompt = (
                "You will get some data, please generate a calendar description for it."
                "Don't mention any start and end time information, nor id info."
                "Please properly describe what the event or action taken is."
                "Prioritize bullet list formatting."
            )
            llm.system_prompt = base_prompt + system_prompt
            description = llm.generate_response(saved_data).content

            start_time = datetime.now(get_localzone())
            if "start_time" in data and isinstance(data["start_time"], str):
                start_time = datetime.fromisoformat(data["start_time"]).replace(
                    tzinfo=get_localzone()
                )

            end_time = start_time + timedelta(minutes=45)
            if "end_time" in data and isinstance(data["end_time"], str):
                end_time = datetime.fromisoformat(data["end_time"]).replace(
                    tzinfo=get_localzone()
                )

            response = gcal.add_event(
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                calendar_id=calendar_id,
            )

            self.saved_calendar_data.append(
                {
                    "title": title,
                    "description": description,
                    "start_time": start_time,
                    "end_time": end_time,
                }
            )

            logger.info("response uploading info to gcal: %s", response)

    async def send_saved_data_notification(self):
        if len(self.saved_calendar_data) == 0:
            logger.error("Did not save any information to calendar.")
            return

        saved_information = ", ".join(
            [f"{data['title']}" for data in self.saved_calendar_data]
        )
        saved_message = render_jinja_template(
            "success.jinja",
            "zootopia/manager/save/templates",
            saved_information=saved_information.replace("\n", ""),
        )
        self.database.insert(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE,
            {"id": self.database.user_id, "from_bot": True, "message": saved_message},
        )
        return await self.messaging_service.send_message(saved_message)
