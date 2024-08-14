from fastapi import APIRouter, HTTPException, Security
from zootopia.api.security import verify_api_key
from zootopia.core.logger import logger
from zootopia.core.schema import SignupRequestBase, Tables, Message
from zootopia.core.exceptions import RoomAlreadyExistsError, AgentNotFoundError
from zootopia.controller.context import SignupContextManager

router = APIRouter()


@router.post("/signup")
async def signup_webhook(
    request: SignupRequestBase, api_key: str = Security(verify_api_key)
):
    try:
        context = SignupContextManager()

        agent = context.get_agent(request.agent_id)
        user, room, is_new_user = context.get_or_create_user_and_room(
            request.user_phone, request.agent_id, request.birthday
        )

        context.messaging_service.set_user_phone(request.user_phone)
        context.messaging_service.set_channel_id(agent.bird_channel_id)
        await context.messaging_service.send_message(agent.first_message)

        context.database.insert(
            table_name=Tables.MESSAGES.value,
            item=Message(
                room_id=room.id,
                sender_id=agent.id,
                content=agent.first_message,
                type="revive",
            ),
        )

    except RoomAlreadyExistsError as rae:
        logger.warning(f"Room already exists: {str(rae)}")
        raise HTTPException(
            status_code=409,
            detail={"error_code": "RoomAlreadyExists", "message": str(rae)},
        )
    except AgentNotFoundError as anf:
        logger.error(f"Agent not found: {str(anf)}")
        raise HTTPException(
            status_code=404, detail={"error_code": "AgentNotFound", "message": str(anf)}
        )
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))
