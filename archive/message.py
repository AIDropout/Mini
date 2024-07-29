from fastapi import APIRouter, Request, HTTPException
from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import MessageContextManager
from zootopia.core.logger import logger
from zootopia.core.schema import RespondTask

router = APIRouter()


@router.post("/message")
async def message_webhook(request: Request):
    try:
        request_body = await request.json()
        logger.info(f"Received request body: {request_body}")

        context = MessageContextManager(config, request_body)
        task = RespondTask(context.message)
        agent = Agent.from_config(config, context)

        await agent.handle_chat_task(task)
    except Exception as e:
        logger.exception("Error in message_webhook")
        raise HTTPException(status_code=500, detail=str(e))
