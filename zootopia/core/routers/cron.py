from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from config.config import config
from zootopia.agent.agent import Agent
from zootopia.context import CronContextManager
from zootopia.core.logger import logger
from zootopia.storage.database.supabase import SupabaseDB
from datetime import datetime, timedelta, timezone
from zootopia.core.schema import Tables, ReviveTask
import traceback
import random
from datetime import datetime, timedelta
from zootopia.core.routers.auth import verify_api_key

router = APIRouter()

async def process_send(agent_id: int, user_id: int, room_id: int):
    context = CronContextManager(config, agent_id, user_id, room_id)
    agent = Agent.from_config(config, context)
    task = ReviveTask()
    await agent.handle_chat_task(task)

def should_send_proactive_message(
    agent_proactivity: float,
    last_message_time: datetime,
    min_interval: timedelta = timedelta(minutes=30),
    max_interval: timedelta = timedelta(days=7)
) -> bool:
    """
    Determine if the agent should send a proactive message based on proactivity and time elapsed.

    Args:
    agent_proactivity - The agent's proactivity score (0 to 1).
    last_message_time - The timestamp of the last message in the room.
    min_interval - The minimum interval between messages.
    max_interval - The maximum interval between messages.

    Returns:
    bool: True if the agent should send a message, False otherwise.
    """
    current_time = datetime.now(timezone.utc)
    time_elapsed = current_time - last_message_time

    # Calculate how much of the total possible interval has elapsed
    interval_progress = (time_elapsed - min_interval) / (max_interval - min_interval)
    interval_progress = max(0, min(interval_progress, 1))  # Clamp between 0 and 1

    # Combine interval progress with agent proactivity
    send_probability = interval_progress * agent_proactivity

    return random.random() < send_probability

@router.post("/cron")
async def cron_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,     
    api_key: str = Security(verify_api_key)
):
    """ Function called every x minutes by Cron service
    
    Sends a message based on a room's time since last message + proactivity of that particular room.

    TODO: Send messages for remind events
    
    """
    try: 
        db: SupabaseDB = SupabaseDB.from_config(config.DATABASE_CONFIG.SUPABASE)

        # Get all agents
        agents = db.query(Tables.AGENTS.value)

        for agent in agents:
            # Get all rooms for this agent where proactivity > 0
            rooms = db.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0)
            )

            for room in rooms:
                # Get the last message in the room
                last_message = db.get_row(
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
                        background_tasks.add_task(process_send, room.agent_id, room.user_id, room.id)

    except Exception as e:
        logger.exception("Error in proactive_webhook")
        raise HTTPException(status_code=500, detail=str(e))