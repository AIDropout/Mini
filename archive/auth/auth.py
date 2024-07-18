"""Configures room info in the database class"""
from datetime import datetime, timezone
from typing import Union
from oauth2client.client import OAuth2Credentials
from config.config import config
from archive.autodb_config.models import GAuthTable, Tables, UserModel, AgentModel, RoomModel
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.apis.gsuite.gauth.gauth import GAuth
from zootopia.messaging.messaging  import MessageProviderBase
from zootopia.messaging.models import ZootopiaMessage, MessageProvider, TelegramMetadata, BirdMetadata
from zootopia.core.logger import logger
from zootopia.core.utils.utils import render_jinja_template


class AuthManager:
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


    def verify_gauth_in_database(self) -> bool:
        data, _ = self.database.get_rows(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.GAUTH, max_rows=1
        )

        if len(data[1]) == 0:
            return False

        user_creds = data[1][0]
        creds = OAuth2Credentials(
            access_token=user_creds["access_token"],
            client_id=config.CALENDAR_CONFIG.GOOGLE.GOOGLE_CLIENT_ID,
            client_secret=config.CALENDAR_CONFIG.GOOGLE.GOOGLE_CLIENT_SECRET,
            refresh_token=user_creds["refresh_token"],
            token_expiry=datetime.fromisoformat(user_creds["token_expiry"]).replace(
                tzinfo=None
            ),
            token_uri=user_creds["token_uri"],
            user_agent=user_creds["user_agent"],
        )

        if creds.access_token_expired:
            return False

        self.creds = creds
        return True

    async def send_welcome_message(self):
        signup_message = render_jinja_template(
            "signup.jinja",
            "zootopia/manager/signup/templates",
            user_name=self.message.user_name,
        )
        self.database.insert(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE,
            {"id": self.database.user_id, "from_bot": True, "message": signup_message},
        )
        return await self.messaging_service.send_message(signup_message)

    async def auth_google(self):
        gauth = GAuth.from_config(config.CALENDAR_CONFIG.GOOGLE)
        auth_url = gauth.get_auth_url()
        gauth_message = render_jinja_template(
            "gauth.jinja", "zootopia/manager/signup/templates", gauth_url=auth_url
        )
        try:
            potential_auth_code = self.message.message.message.text
            creds = gauth.authenticate_with_code(potential_auth_code)
        except Exception as e:
            logger.info(  # pylint: disable=W1203
                f"An error occured while authenticating with Google: {e}"
            )
            return await self.messaging_service.send_message(gauth_message)

        self.creds = creds
        gauth_table = config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.GAUTH
        gauth_row = GAuthTable(
            access_token=creds.access_token,
            refresh_token=creds.refresh_token,
            token_expiry=creds.token_expiry.astimezone(timezone.utc).isoformat(),
            token_uri=creds.token_uri,
            user_agent=creds.user_agent,
        )
        json_gauth = gauth_row.model_dump()
        json_gauth[config.DATABASE_CONFIG.CONSTANT_IDS.ID_COLUMN_NAME] = (
            self.database.user_id
        )
        self.database.insert(gauth_table, json_gauth)

    async def send_successful_auth_message(self):
        signup_message = render_jinja_template(
            "success.jinja",
            "zootopia/manager/signup/templates",
            user_name=self.message.user_name,
        )
        self.database.insert(
            config.DATABASE_CONFIG.CONSTANT_IDS.TABLE_IDS.MESSAGE,
            {"id": self.database.user_id, "from_bot": True, "message": signup_message},
        )
        return await self.messaging_service.send_message(signup_message)
