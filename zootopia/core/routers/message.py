from fastapi import APIRouter, Request
import json
import traceback

from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import MessageContextManager
from zootopia.agent.tasks import ChatTaskType
from zootopia.core.logger import logger

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request):
    try: 
        request_body = await request.json()
        logger.info(f"Received request body: {request_body}")
        task_type = request_body.get('task_type', ChatTaskType.RESPOND)

        context = MessageContextManager(config, request_body)
        agent = Agent.from_config(context, config)

        if task_type == ChatTaskType.RESPOND:
            await agent.respond_to_user()
        elif task_type == ChatTaskType.REVIVE:
            await agent.revive_chat()
        elif task_type == ChatTaskType.SCHEDULED:
            await agent.handle_scheduled_task()
        else:
            logger.warning(f"Unhandled task type: {task_type}")
            return {"message": f"Unhandled task type: {task_type}"}

    except Exception as e:
        logger.error(f"Error in message_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"message": "Error occurred", "error": str(e)}
    
    return {"message": f"Received and processed {task_type} task"}