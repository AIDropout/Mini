from typing import Union

from mini.manager.messaging.bird.bird import BirdManager 
from mini.manager.messaging.telegram import TelegramManager


class MessagingManagerFactory:
    def __init__(self):
        self._bird_manager = None
        self._telegram_manager = None

    def get_manager_from_request(
        self, request_body: dict
    ) -> Union[BirdManager, TelegramManager]:
        """Takes a request body from a messaging provider and returns the proper manager"""
        if "payload" in request_body:
            return self.bird_manager
        elif "update_id" in request_body:
            return self.telegram_manager
        else:
            return self.bird_manager

    @property
    def bird_manager(self) -> BirdManager:
        if self._bird_manager is None:
            self._bird_manager = BirdManager()
        return self._bird_manager

    @property
    def telegram_manager(self) -> TelegramManager:
        if self._telegram_manager is None:
            self._telegram_manager = TelegramManager()
        return self._telegram_manager
