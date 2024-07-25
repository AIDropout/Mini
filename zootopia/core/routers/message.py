from fastapi import APIRouter, Request
import json
import traceback

from config.config import config
from zootopia.agent import Agent, ContextManager
from zootopia.core.logger import logger

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request):
    try: 
        request_body = json.loads(await request.body())
        logger.info(f"Received request body: {request_body}")

        context = ContextManager.from_config(request_body, config)
        agent = Agent.from_config(context, config)
        await agent.respond_to_user()
    except Exception as e:
        logger.error(f"Error in message_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {"message": "Received"}