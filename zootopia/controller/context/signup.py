from typing import Optional, Tuple
from zootopia.core.schema import Tables, User, Agent, Room
from zootopia.services import BirdSMSProvider
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError
from zootopia.controller.context import BaseContextManager


class SignupContextManager(BaseContextManager):
    def __init__(self):
        super().__init__()
        self.messaging_service: BirdSMSProvider = BirdSMSProvider()

    def get_agent(self, agent_id: int) -> Agent:
        agent = self.database.get_row(
            Tables.AGENTS.value, conditions={Tables.AGENTS__id.value: agent_id}
        )

        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    def get_or_create_user_and_room(
        self, user_phone: str, agent_id: int, birthday: Optional[str] = None
    ) -> Tuple[User, Room, bool]:
        existing_user = self.database.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__phone_number.value: user_phone},
        )

        if existing_user:
            existing_room = self.database.get_row(
                Tables.ROOMS.value,
                conditions={
                    Tables.ROOMS__user_id.value: existing_user.id,
                    Tables.ROOMS__agent_id.value: agent_id,
                },
            )
            if existing_room:
                raise RoomAlreadyExistsError(user_phone, agent_id)

            new_room = self.database.insert(
                table_name=Tables.ROOMS.value,
                item=Room(user_id=existing_user.id, agent_id=agent_id),
            )
            return existing_user, new_room, False

        new_user = self.database.insert(
            table_name=Tables.USERS.value,
            item=User(phone_number=user_phone, birthday=birthday),
        )
        new_room = self.database.insert(
            table_name=Tables.ROOMS.value,
            item=Room(user_id=new_user.id, agent_id=agent_id),
        )
        return new_user, new_room, True
