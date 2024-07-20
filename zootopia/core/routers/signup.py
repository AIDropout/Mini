from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Tuple
import traceback

from config.config import config
from zootopia.core.logger import logger
from zootopia.core.schema import Tables, UserTableModel, AgentTableModel, RoomTableModel, MessageTableModel
from zootopia.storage.database.supabase import SupabaseDB
from zootopia.platform.platform import MessageProviderBase
from zootopia.platform.sms.bird import BirdSMSProvider
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError

router = APIRouter()

class SignupRequestBase(BaseModel):
    agent_id: int
    user_phone: str
    birthday: Optional[str] = None

def get_or_create_agent(agent_id: int, database: SupabaseDB) -> AgentTableModel:
    agent = database.get_row(
        Tables.AGENTS.value,
        conditions={Tables.AGENTS__id.value: agent_id}
    )
    if not agent:
        raise AgentNotFoundError(agent_id)
    return agent

def get_or_create_user_and_room(request: SignupRequestBase, agent: AgentTableModel, database: SupabaseDB) -> Tuple[UserTableModel, RoomTableModel, bool]:
    existing_user = database.get_row(
        Tables.USERS.value,
        conditions={Tables.USERS__phone_number.value: request.user_phone}
    )

    if existing_user:
        existing_room = database.get_row(
            Tables.ROOMS.value,
            conditions={
                Tables.ROOMS__user_id.value: existing_user.id,
                Tables.ROOMS__agent_id.value: agent.id
            }
        )
        if existing_room:
            raise RoomAlreadyExistsError(request.user_phone, request.agent_id)
        
        new_room = database.insert(table_name=Tables.ROOMS.value, item=RoomTableModel(
            user_id=existing_user.id,
            agent_id=agent.id
        ))
        return existing_user, new_room, False

    new_user = database.insert(table_name=Tables.USERS.value, item=UserTableModel(
        phone_number=request.user_phone,
        birthday=request.birthday
    ))
    new_room = database.insert(table_name=Tables.ROOMS.value, item=RoomTableModel(
        user_id=new_user.id,
        agent_id=agent.id
    ))
    return new_user, new_room, True

@router.post("/signup")
async def signup_webhook(request: SignupRequestBase):
    try: 
        database: SupabaseDB = SupabaseDB.from_config(config.DATABASE_CONFIG.SUPABASE)
        sms_service: BirdSMSProvider = BirdSMSProvider.from_config(config.MESSAGING_CONFIG.BIRD)
        
        agent = get_or_create_agent(request.agent_id, database)
        user, room, is_new_user = get_or_create_user_and_room(request, agent, database)

        sms_service.set_user_phone(request.user_phone)
        sms_service.set_channel_id(agent.bird_channel_id)
        await sms_service.send_message(agent.first_message)
        
        database.insert(table_name=Tables.MESSAGES.value, item=MessageTableModel(
            room_id=room.id,
            from_user=False,
            message=agent.first_message
        ))

        return {"message": "Signup successful"}
    except RoomAlreadyExistsError as rae:
        logger.warning(f"Room already exists: {str(rae)}")
        raise HTTPException(status_code=409, detail={"error_code": "RoomAlreadyExists", "message": str(rae)})
    except AgentNotFoundError as anf:
        logger.error(f"Agent not found: {str(anf)}")
        raise HTTPException(status_code=404, detail={"error_code": "AgentNotFound", "message": str(anf)})
    except Exception as e:
        logger.error(f"Unexpected error in signup_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"error_code": "InternalServerError", "message": "An unexpected error occurred"})