from typing import Optional, Tuple
from fastapi import HTTPException
from zootopia.core.schema import Tables, User, Agent, Room, Message, SignupRequest
from zootopia.manager.messaging import BirdManager
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError
from zootopia.manager.database import DatabaseManager
from zootopia.core.logger import logger
from zootopia.service.base import Service


class SignupService(Service):
    def __init__(
        self, database_manager: DatabaseManager, messaging_manager: BirdManager
    ):
        super().__init__(database_manager)
        self.messaging_manager = messaging_manager

    def process_signup(self, request: SignupRequest):
        """Creates a new room for the user with the selected agent & sends the first message"""
        try:
            agent = self.get_agent(request.agent_id)
            user, room, is_new_user = self.get_or_create_user_and_room(
                request.user_phone, request.agent_id, request.birthday
            )

            self.messaging_manager.set_user_phone(request.user_phone)
            self.messaging_manager.set_channel_id(agent.bird_channel_id)
            self.messaging_manager.send_message(agent.first_message)

            self.database_manager.insert(
                table_name=Tables.MESSAGES.value,
                item=Message(
                    room_id=room.id,
                    sender_id=agent.id,
                    content=agent.first_message,
                    type="revive",
                ),
            )

            return {"status": "success", "is_new_user": is_new_user}

        except RoomAlreadyExistsError as rae:
            logger.warning(f"Room already exists: {str(rae)}")
            raise HTTPException(
                status_code=409,
                detail={"error_code": "RoomAlreadyExists", "message": str(rae)},
            )
        except AgentNotFoundError as anf:
            logger.error(f"Agent not found: {str(anf)}")
            raise HTTPException(
                status_code=404,
                detail={"error_code": "AgentNotFound", "message": str(anf)},
            )
        except Exception as e:
            logger.exception("Error in signup process")
            raise HTTPException(status_code=500, detail=str(e))

    def get_agent(self, agent_id: int) -> Agent:
        agent = self.database_manager.get_row(
            Tables.AGENTS.value, conditions={Tables.AGENTS__id.value: agent_id}
        )

        if not agent:
            raise AgentNotFoundError(agent_id)
        return agent

    def get_or_create_user_and_room(
        self, user_phone: str, agent_id: int, birthday: Optional[str] = None
    ) -> Tuple[User, Room, bool]:
        existing_user = self.database_manager.get_row(
            Tables.USERS.value,
            conditions={Tables.USERS__phone_number.value: user_phone},
        )

        if existing_user:
            existing_room = self.database_manager.get_row(
                Tables.ROOMS.value,
                conditions={
                    Tables.ROOMS__user_id.value: existing_user.id,
                    Tables.ROOMS__agent_id.value: agent_id,
                },
            )
            if existing_room:
                raise RoomAlreadyExistsError(user_phone, agent_id)

            new_room = self.database_manager.insert(
                table_name=Tables.ROOMS.value,
                item=Room(user_id=existing_user.id, agent_id=agent_id),
            )
            return existing_user, new_room, False

        new_user = self.database_manager.insert(
            table_name=Tables.USERS.value,
            item=User(phone_number=user_phone, birthday=birthday),
        )
        new_room = self.database_manager.insert(
            table_name=Tables.ROOMS.value,
            item=Room(user_id=new_user.id, agent_id=agent_id),
        )
        return new_user, new_room, True
