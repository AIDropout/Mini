
from typing import Optional, Tuple
from zootopia.core.schema import Tables, UserTableModel, AgentTableModel, RoomTableModel
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError
from zootopia.context import BaseContextManager

class SignupContextManager(BaseContextManager):
    def __init__(self, config):
        super().__init__(config)
        self.bird_sms: BirdSMSProvider = BirdSMSProvider.from_config(self.config.MESSAGING_CONFIG.BIRD)

    def get_agent(self, agent_id: int) -> AgentTableModel:
        agent = self.database.get_row(
            Tables.AGENTS.value,
            conditions={Tables.AGENTS__id.value: agent_id}
        )
        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    def get_or_create_user_and_room(self, user_phone: str, agent_id: int, birthday: Optional[str] = None) -> Tuple[UserTableModel, RoomTableModel, bool]:
        existing_user = self.database.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__phone_number.value: user_phone}
        )

        if existing_user:
            existing_room = self.database.get_row(
                Tables.ROOMS.value,
                conditions={
                    Tables.ROOMS__user_id.value: existing_user.id,
                    Tables.ROOMS__agent_id.value: agent_id
                }
            )
            if existing_room:
                raise RoomAlreadyExistsError(user_phone, agent_id)
            
            new_room = self.database.insert(table_name=Tables.ROOMS.value, item=RoomTableModel(
                user_id=existing_user.id,
                agent_id=agent_id
            ))
            return existing_user, new_room, False

        new_user = self.database.insert(table_name=Tables.USERS.value, item=UserTableModel(
            phone_number=user_phone,
            birthday=birthday
        ))
        new_room = self.database.insert(table_name=Tables.ROOMS.value, item=RoomTableModel(
            user_id=new_user.id,
            agent_id=agent_id
        ))
        return new_user, new_room, True
