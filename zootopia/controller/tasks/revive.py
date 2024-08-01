from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, Security
from zootopia.core.logger import logger
from zootopia.database import SupabaseDB
from datetime import datetime, timedelta, timezone
from zootopia.core.schema import Tables, TaskType
import traceback
import random
from datetime import datetime, timedelta
from zootopia.core.security import verify_api_key
from zootopia.controller.tasks.tasks import process_task


async def handle_revive(background_tasks: BackgroundTasks):
    """Function called every x minutes by Cron service

    Sends a message based on a room's time since last message + proactivity of that particular room.

    TODO: Send messages for remind events

    """
    try:

        db: SupabaseDB = SupabaseDB()

        # Get all agents
        agents = db.query(Tables.AGENTS.value)

        for agent in agents:
            # Get all rooms for this agent where proactivity > 0
            rooms = db.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0),
            )

            for room in rooms:
                # If a scheduled reminder in the db
                # task_data = {
                #     "type": TaskType.REMIND.value,
                #     "room_id": room.id,
                # }
                # background_tasks.add_task(process_task, task_data)

                # Get the last message in the room
                last_message = db.get_row(
                    Tables.MESSAGES.value,
                    {Tables.MESSAGES__room_id.value: room.id},
                    order_by=Tables.MESSAGES__created_at.value,
                    order_desc=True,
                )

                if last_message:
                    if should_send_proactive_message(
                        agent_proactivity=room.agent_proactivity,
                        last_message_time=last_message.created_at,
                    ):
                        task_data = {
                            "type": TaskType.REVIVE.value,
                            "room_id": room.id,
                        }
                        background_tasks.add_task(process_task, task_data)
    except Exception as e:
        tb_str = traceback.format_exception(type(e), e, e.__traceback__)
        full_traceback = "".join(tb_str)
        logger.error(f"Error in process_agents: {full_traceback}")
        raise Exception(f"An error occurred: {str(e)}\n\nTraceback:\n{full_traceback}")


def should_send_proactive_message(
    agent_proactivity: float,
    last_message_time: datetime,
    min_interval: timedelta = timedelta(minutes=30),
    max_interval: timedelta = timedelta(days=7),
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
