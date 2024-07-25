from fastapi import APIRouter, Request
import json
import traceback

from config.config import config
from zootopia.agent import AgentController, ContextManager
from zootopia.core.logger import logger

router = APIRouter()

"""
This endpoint is called every x minutes by an external cron job service

There are two types of proactive messages.

1) Out of nowhere "Chat revivers" i.e. if the chat has gone silent
2) Scheduled messages i.e. Saying happy birthday 
"""


@router.post("/proactive")
async def proactive_webhook(request: Request):
    try: 

        request_body = json.loads(await request.body())


        # Chat responder (reactive)
        # Get past messages + incoming message, formulate response, send it

        # Chat reviver (proactive)
        # Get past messages + context about chat silence, formulate response, send it

        # Chat scheduler (proactive)
        # Get past messages + scheduled context, formulate response, send it




        # logger.info(f"Received request body: {request_body}")

        # context = ContextManager.from_config(request_body, config)

        # zootopian = AgentController.from_config(context, config)

        # await zootopian.handle_message()
    except Exception as e:
        logger.error(f"Error in webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    
    return {"message": "Received"}