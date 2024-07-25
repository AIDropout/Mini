from fastapi import APIRouter, HTTPException
import traceback

from config.config import config
from zootopia.core.logger import logger
from zootopia.core.schema import SignupRequestBase, Tables, MessageTableModel
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError
from zootopia.context import SignupContextManager

router = APIRouter()

@router.post("/signup")
async def signup_webhook(request: SignupRequestBase):
    try:
        context = SignupContextManager(config)
        
        agent = context.get_agent(request.agent_id)
        user, room, is_new_user = context.get_or_create_user_and_room(request.user_phone, request.agent_id, request.birthday)
        
        context.bird_sms.set_user_phone(request.user_phone)
        context.bird_sms.set_channel_id(agent.bird_channel_id)
        await context.bird_sms.send_message(agent.first_message)
        
        context.database.insert(table_name=Tables.MESSAGES.value, item=MessageTableModel(
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