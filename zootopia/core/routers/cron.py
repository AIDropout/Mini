from fastapi import APIRouter, Request, BackgroundTasks
from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import MessageContextManager
from zootopia.core.logger import logger
from zootopia.storage.database.supabase import SupabaseDB
from datetime import datetime, timedelta, timezone
from zootopia.core.schema import Tables
import traceback
import random
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/cron")
async def cron_webhook(request: Request, background_tasks: BackgroundTasks):
    """ Function called every x minutes by Cron service
    
    Sends a message based on a room's time since last message + proactivity of that particular room.

    TODO: Send messages for scheduled events
    
    """
    try: 
        request_body = await request.json()
        logger.info(f"Received request body: {request_body}")

        database: SupabaseDB = SupabaseDB.from_config(config.DATABASE_CONFIG.SUPABASE)

        # Get all agents
        agents = database.query(Tables.AGENTS.value)

        for agent in agents:
            logger.info(f"agent id: {agent.id}")

            # Get all rooms for this agent where proactivity > 0
            rooms = database.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0)
            )

            for room in rooms:
                logger.info(f"room id: {room.id}")
                # Get the last message in the room
                last_message = database.get_row(
                    Tables.MESSAGES.value,
                    {Tables.MESSAGES__room_id.value: room.id},
                    order_by=Tables.MESSAGES__created_at.value,
                    order_desc=True
                )

                if last_message:
                    if should_send_proactive_message(
                        agent_proactivity=room.agent_proactivity,
                        last_message_time=last_message.created_at
                    ):
                        # Add a background task to send the message
                        background_tasks.add_task(process_send, room.id, room.user_id, agent.id)



        return {"message": "Proactive messages processed"}
    except Exception as e:
        logger.error(f"Error in proactive_webhook: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"message": "Error occurred", "error": str(e)}

async def process_send(room_id: int, user_id: int, agent_id: int):
    try:
        context = MessageContextManager(config, {
            "room_id": room_id,
            "user_id": user_id,
            "agent_id": agent_id
        })
        agent = Agent.from_config(context, config)
        await agent.revive_chat()
    except Exception as e:
        logger.error(f"Error sending proactive message: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")

def should_send_proactive_message(
    agent_proactivity: float,
    last_message_time: datetime,
    min_interval: timedelta = timedelta(minutes=30),
    max_interval: timedelta = timedelta(days=7)
) -> bool:
    """
    Determine if the agent should send a proactive message based on proactivity and time elapsed.

    Args:
    agent_proactivity (float): The agent's proactivity score (0 to 1).
    last_message_time (datetime): The timestamp of the last message in the room.
    min_interval (timedelta): The minimum interval between messages (default 30 minutes).
    max_interval (timedelta): The maximum interval between messages (default 7 days).

    Returns:
    bool: True if the agent should send a message, False otherwise.
    """
    current_time = datetime.now(timezone.utc)
    time_elapsed = current_time - last_message_time

    # Calculate the actual interval based on proactivity
    actual_interval = max_interval - (max_interval - min_interval) * agent_proactivity

    # Calculate the probability of sending a message
    if time_elapsed < actual_interval:
        # Reduce probability if less time has passed than the actual interval
        probability = (time_elapsed / actual_interval) * agent_proactivity
    else:
        # Full probability if more time has passed than the actual interval
        probability = agent_proactivity

    # Add some randomness
    return random.random() < probability