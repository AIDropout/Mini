from zootopia.brain.communicate.communicate import CommunicateManager
from zootopia.brain.models import Intents
from zootopia.brain.save.save import SaveManager
from zootopia.brain.auth.auth import AuthManager
from zootopia.brain.auth.auth import AuthManager
from zootopia.brain.upload.upload import UploadManager
from zootopia.messaging.models import MessageType
from zootopia.messaging.messaging  import MessageProviderBase
from zootopia.messaging.models import ZootopiaMessage, MessageType
from zootopia.utils.logger import logger
from zootopia.handler.context import ZootopiaContext



class DigitalBrain:
    def __init__(
        self, context: ZootopiaContext
    ) -> None:
        self.ZOOTOPIA = context
        self.sm = AuthManager(context)
        self.up = UploadManager(context)
        self.cm = CommunicateManager(context)
        self.sv = SaveManager(context)


    async def detect_intent(self) -> Intents:

        if self.sm.verify_gauth_in_database() is False:
            logger.info("User has unauthenticated Google account.")
            await self.sm.auth_google()
            if self.sm.creds is not None:
                await self.sm.send_successful_auth_message()
            return Intents.AUTH_GOOGLE

        if self.ZOOTOPIA.message.type is MessageType.FILE:
            logger.info("User sent a file.")
            self.up.creds = self.sm.creds
            await self.up.upload_to_drive()
            self.up.save_upload_url_to_calendar()
            await self.up.send_uploaded_notification()
            return Intents.SAVE_FILE

        # add relavent data to database
        self.sv.save_data_using_autodb()
        self.sv.save_user_message_to_db()

        if self.sv.user_wants_to_save_data():
            logger.info("User wants to save data.")
            self.sv.creds = self.sm.creds
            self.sv.save_data_to_calendar()
            await self.sv.send_saved_data_notification()

        self.cm.get_relevant_user_data()
        self.cm.get_past_conversation()
        await self.cm.send_llm_response_message()
        return Intents.ANSWER_QUERY

    async def simple_response(self):
        if self.sm.configure_room() is False:
            # logger.info("User is not signed up yet.")
            # self.sm.save_user_to_database()
            # await self.sm.send_welcome_message()
            return Intents.USER_SIGNUP

        self.cm.get_past_conversation()
        await self.cm.send_llm_response_message()
        return Intents.ANSWER_QUERY
