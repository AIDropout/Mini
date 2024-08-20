from fastapi import HTTPException
from zootopia.core.schema.tables import Tables, User, Agent, Room, Message
from zootopia.manager.messaging import BirdManager
from zootopia.manager.database import DatabaseManager
from zootopia.manager.payment import CustomerManager
from zootopia.core.logger import logger
from zootopia.service.base import Service
from zootopia.service.user_service import UserService
from zootopia.core.schema.task import TaskType
from typing import Optional


class RoomService(Service):
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_manager: BirdManager,
        customer_manager: CustomerManager,
        user_service: UserService,
    ):
        super().__init__(database_manager)
        self.messaging_manager = messaging_manager
        self.customer_manager = customer_manager
        self.user_service = user_service

    async def create_room(self, agent_id: str, user_id: str) -> Room:
        """Creates a new room & sends the first message"""

        try:
            agent = self._get_agent(agent_id)
            user = self.user_service.get_user(user_id)
            existing_room = self.get_room(agent_id, user_id)
            if existing_room:
                raise HTTPException(
                    status_code=409, detail="User already has a chat with this agent"
                )
            
            self.messaging_manager.set_receiver(user.phone_number)
            self.messaging_manager.set_sender(agent.bird_channel_id)
            await self.messaging_manager.send_message(agent.first_message)

            new_room = self.database_manager.insert(
                table_name=Tables.ROOMS,
                item=Room(user_id=user_id, agent_id=agent_id),
            )

            self.database_manager.insert(
                table_name=Tables.MESSAGES,
                item=Message(
                    room_id=new_room.id,
                    sender_id=agent_id,
                    content=agent.first_message,
                    type=TaskType.REVIVE,
                ),
            )

            return new_room
        except Exception as e:
            logger.exception("Error in room creation process")
            raise HTTPException(status_code=500, detail=str(e))

    def get_room(self, agent_id: str, user_id: str) -> Optional[Room]:
        """Retrieves a room by agent_id and user_id"""

        room = self.database_manager.get_row(
            Tables.ROOMS,
            conditions={
                Tables.ROOMS__agent_id: str(agent_id),
                Tables.ROOMS__user_id: str(user_id),
            },
        )
        return room  # Return None if room is not found

    def get_room_or_error(self, agent_id: str, user_id: str) -> Room:
        """Retrieves a room by agent_id and user_id, raising an error if not found"""

        room = self.get_room(agent_id, user_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        return room


    def _get_agent(self, agent_id: str) -> Agent:
        """Retrieves an agent by id"""

        agent = self.database_manager.get_row(
            Tables.AGENTS, conditions={Tables.AGENTS__id: agent_id}
        )

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent
