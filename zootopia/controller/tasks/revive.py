from fastapi import BackgroundTasks
from zootopia.core.logger import logger
from zootopia.database import SupabaseDB
from zootopia.core.schema import (
    Tables,
    AgentTableModel,
    RoomTableModel,
    MessageTableModel,
)
from zootopia.utils.time_utils import should_send_proactive_message
from zootopia.controller.tasks.task_processor import process_task
from zootopia.controller.tasks.task_types import ReviveTask, ScheduledTaskInfo


async def handle_revive(background_tasks: BackgroundTasks, dev_mode: bool = False):
    """
    Function called periodically by Cron service to send proactive messages
    based on room's last message time and agent's proactivity.
    """
    try:
        db = SupabaseDB()
        
        if dev_mode:
            agents = db.query(Tables.AGENTS.value, ("id", "=", 1))
        else:
            agents = db.query(Tables.AGENTS.value)

        for agent in agents:
            await process_agent_rooms(db, agent, background_tasks)
    except Exception as e:
        logger.error(f"Error in handle_revive: {str(e)}", exc_info=True)
        raise


async def process_agent_rooms(
    db: SupabaseDB, agent: AgentTableModel, background_tasks: BackgroundTasks
):
    proactive_rooms = get_proactive_rooms(db, agent.id)

    for room in proactive_rooms:
        last_message = get_last_message(db, room.id)
        if last_message and should_revive_room(room, last_message):
            schedule_revive_task(room.id, background_tasks)


def get_proactive_rooms(db: SupabaseDB, agent_id: int):
    return db.query(
        Tables.ROOMS.value,
        (Tables.ROOMS__agent_id.value, agent_id),
        (Tables.ROOMS__agent_proactivity.value, ">", 0),
    )


def get_last_message(db: SupabaseDB, room_id: int):
    return db.get_row(
        Tables.MESSAGES.value,
        {Tables.MESSAGES__room_id.value: room_id},
        order_by=Tables.MESSAGES__created_at.value,
        order_desc=True,
    )


def should_revive_room(room: RoomTableModel, last_message: MessageTableModel) -> bool:
    return should_send_proactive_message(
        agent_proactivity=room.agent_proactivity,
        last_message_time=last_message.created_at,
    )


def schedule_revive_task(room_id: int, background_tasks: BackgroundTasks):
    revive_task = ReviveTask(room_id=room_id)
    scheduled_task_info = ScheduledTaskInfo(task=revive_task, delay=0)
    background_tasks.add_task(process_task, scheduled_task_info.to_dict())
    logger.info(f"Scheduled revive task for room {room_id}")
