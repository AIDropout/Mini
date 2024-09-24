from typing import List, Optional

from fastapi import HTTPException

from mini.core.logger import get_logger
from mini.database.models import Agent, Message, Room, Tables
from mini.database.database import DatabaseManager
from mini.messaging.providers.bird import BirdMessaging
from mini.payment.stripe.customer import CustomerManager
from mini.database.service.user_service import UserService
from mini.messaging.providers.bird.vcard import get_or_create_contact_card

logger = get_logger(__name__)


class RoomService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        messaging_provider: BirdMessaging,
        customer_manager: CustomerManager,
        user_service: UserService,
    ):
        self.database_manager = database_manager
        self.messaging_provider = messaging_provider
        self.customer_manager = customer_manager
        self.user_service = user_service

    def create_room(self, agent_id: str, user_id: str) -> Room:
        """Creates a new room & sends the first message"""

        try:
            # Check if the room already exists
            room = self.get_room(agent_id, user_id)
            if room:
                raise HTTPException(
                    status_code=409, detail="User already has a chat with this agent"
                )

            # Fetch the agent and user
            agent = self._get_agent(agent_id)
            user = self.user_service.get_user(user_id)

            # Send the first message
            self.messaging_provider.set_receiver(user.phone_number)
            self.messaging_provider.set_sender(agent.bird_channel_id)

            # Get agent phone number
            channel = self.database_manager.get_row(
                Tables.CHANNELS,
                {Tables.CHANNELS__id: agent.bird_channel_id},
            )

            file_url = get_or_create_contact_card(
                agent_id=agent_id, db_manager=self.database_manager
            )

            # Send file
            self.messaging_provider.send_message(
                text=agent.first_message, files=[(file_url, "text/vcard")]
            )

            # Create a new room
            new_room = self.database_manager.insert(
                table_name=Tables.ROOMS,
                item=Room(user_id=user_id, agent_id=agent_id),
            )

            # Log the initial message
            self.database_manager.insert(
                table_name=Tables.MESSAGES,
                item=Message(
                    room_id=new_room.id,
                    sender_id=agent_id,
                    content=agent.first_message,
                ),
            )

            return new_room

        except Exception as e:
            logger.exception("Error in room creation process")
            raise HTTPException(status_code=500, detail=str(e))

    def get_room(
        self, agent_id: str, user_id: str, raise_error: bool = False
    ) -> Optional[Room]:
        """Retrieves a room by agent_id and user_id, optionally raising an error if not found"""

        room = self.database_manager.get_row(
            Tables.ROOMS,
            conditions={
                Tables.ROOMS__agent_id: agent_id,
                Tables.ROOMS__user_id: user_id,
            },
        )
        if raise_error and not room:
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

    def get_user_rooms(self, user_id: str) -> Optional[List[Room]]:
        rooms = self.database_manager.get_multiple_rows(
            Tables.ROOMS,
            max_rows=20,
            order_by=Tables.ROOMS__created_at,  # TODO: add last msg sent col in ROOM
            order_desc=True,
            conditions={Tables.ROOMS__user_id: user_id},
        )
        if not rooms:
            raise HTTPException(status_code=404, detail="Rooms not found")
        return rooms

    def get_message_count_for_sender(self, room_id: str, sender_id: str) -> int:
        """
        Get the number of messages in the room using a direct count query.
        """
        return self.database_manager.count_rows(
            table_name=Tables.MESSAGES,
            conditions={
                Tables.MESSAGES__room_id: room_id,
                Tables.MESSAGES__sender_id: sender_id,
            },
        )
