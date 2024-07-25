from fastapi import APIRouter, Request
import traceback
from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import MessageContextManager
from zootopia.core.logger import logger

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request):
    try: 
        request_body = await request.json()
        logger.info(f"Received request body: {request_body}")

        context = MessageContextManager(config, request_body)
        agent = Agent.from_config(context, config)

        await agent.respond_to_user()
    except Exception as e:
        logger.error(f"Error in message_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"message": "Error occurred", "error": str(e)}
    
    return {"message": f"Received and processed task"}