from fastapi import APIRouter, Request
import traceback
from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import MessageContextManager
from zootopia.core.logger import logger
from zootopia.core.schema import RespondChatTask

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request):
    try: 
        request_body = await request.json()
        logger.info(f"Received request body: {request_body}")

        context = MessageContextManager(config, request_body)
        task = RespondChatTask(context.message)
        agent = Agent.from_config(config, context)

        await agent.handle_chat_task(task)
    except Exception as e:
        logger.error(f"Error in message_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"message": "Error occurred", "error": str(e)}
    
    return {"message": f"Received and processed task"}