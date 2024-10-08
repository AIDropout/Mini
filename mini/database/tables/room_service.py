from typing import List, Optional

from fastapi import HTTPException, BackgroundTasks

from mini.core.logger import get_logger
from mini.database.models import Agent, Message, Room, Tables
from mini.database.database import DatabaseManager
from mini.messaging.providers.bird import BirdMessaging
from mini.payment.stripe.customer import CustomerManager
from mini.database.tables.user_service import UserTableService
from mini.database.tables.agent_service import AgentTableService
from mini.database.tables.session_service import SessionTableService
from mini.utils.time import TimeManager


logger = get_logger(__name__)


class RoomTableService:
    def __init__(
        self,
        database_manager: DatabaseManager,
        customer_manager: CustomerManager,
        user_table_service: UserTableService,
        agent_table_service: AgentTableService,
        session_table_service: SessionTableService,
        system_time_manager: TimeManager,
    ):
        self.database_manager = database_manager
        self.messaging_provider = BirdMessaging()
        self.customer_manager = customer_manager
        self.user_table_service = user_table_service
        self.agent_table_service = agent_table_service
        self.session_table_service = session_table_service
        self.system_time_manager = system_time_manager

    def create_room(
        self,
        agent_id: str,
        user_id: str,
        background_tasks: BackgroundTasks,
        first_message: Optional[str] = None,
    ) -> Room:
        """Creates a new room & schedules the first message as a background task"""

        try:
            # Check if the room already exists
            room = self.get_room(agent_id, user_id)
            if room:
                raise HTTPException(
                    status_code=409, detail="User already has a chat with this agent"
                )

            # Create a new room
            new_room = self.database_manager.insert(
                table_name=Tables.ROOMS,
                item=Room(user_id=user_id, agent_id=agent_id),
            )

            # Schedule the rest of the operations as a background task
            background_tasks.add_task(
                self._perform_post_room_creation_tasks,
                new_room,
                agent_id,
                user_id,
                first_message
            )

            return new_room

        except Exception as e:
            logger.exception("Error in room creation process")
            raise HTTPException(status_code=500, detail=str(e))

    def _perform_post_room_creation_tasks(
        self,
        room: Room,
        agent_id: str,
        user_id: str,
        first_message: Optional[str]
    ):
        """Performs tasks after room creation as a background process"""
        try:
            # Fetch the agent and user
            agent = self.agent_table_service.get_agent(agent_id)
            user = self.user_table_service.get_user(user_id)

            # Send the first message
            self.messaging_provider.set_receiver(user.phone_number)
            self.messaging_provider.set_sender(agent.bird_channel_id)

            file_url = self.agent_table_service.get_or_create_contact_card(agent.id)

            # First message w/ vcard
            self.messaging_provider.send_message(files=[(file_url, "text/vcard")])
            message_to_send = first_message if first_message is not None else agent.first_message
            self.messaging_provider.send_message(text=message_to_send)

            # Increment agent's room count
            self.database_manager.update(
                Tables.AGENTS.value,
                update_data={Tables.AGENTS__room_count: agent.room_count + 1},
                condition_key=Tables.AGENTS__id,
                condition_value=agent.id,
            )

            # Start a session
            new_session = self.session_table_service.get_or_start_active_session(room.id)

            # Log the initial message
            self.database_manager.insert(
                table_name=Tables.MESSAGES,
                item=Message(
                    room_id=room.id,
                    sender_id=agent.id,
                    content=message_to_send,
                    session_id=new_session.id,
                ),
            )

        except Exception as e:
            logger.exception("Error in post-room creation tasks")
            # Consider implementing a retry mechanism or alerting system here

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

    def get_room_by_id(self, room_id) -> Optional[Room]:
        """Retrieves a room by agent_id and user_id, optionally raising an error if not found"""

        room = self.database_manager.get_row(
            Tables.ROOMS,
            conditions={
                Tables.ROOMS__id: room_id,
            },
        )
        if not room:
            raise HTTPException(
                status_code=404, detail=f"Room not found for id {room_id}"
            )
        return room

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

    def update_room_last_sent(self, room_id: str) -> Room:
        timestamp = self.system_time_manager.get_user_timestamp()

        return self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__last_msg_sent_at: timestamp},
            condition_key=Tables.ROOMS__id,
            condition_value=room_id,
        )

    def update_room_proactivity(self, room_id: str, new_proactivity: float) -> Room:
        return self.database_manager.update(
            Tables.ROOMS,
            {Tables.ROOMS__agent_proactivity: new_proactivity},
            condition_key=Tables.ROOMS__id,
            condition_value=room_id,
        )
