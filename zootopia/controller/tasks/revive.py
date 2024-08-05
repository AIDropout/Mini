from fastapi import BackgroundTasks
from zootopia.core.logger import logger
from zootopia.services import SupabaseDB
from zootopia.core.schema import (
    Tables,
    AgentTableModel,
    RoomTableModel,
    MessageTableModel,
)
from zootopia.utils.time_utils import should_send_proactive_message
from zootopia.controller.tasks.task_scheduler import TaskScheduler
from zootopia.controller.tasks.task_types import ReviveTask, ScheduledTaskInfo


def handle_revive(background_tasks: BackgroundTasks, dev_mode: bool = False):
    """
    Function called periodically by Cron service to send proactive messages
    based on room's last message time and agent's proactivity.
    """
    try:
        db = SupabaseDB()

        # Query agents (all or just one for dev mode)
        agents = db.query(Tables.AGENTS.value, ("id", "=", 1) if dev_mode else None)

        for agent in agents:
            # Get all proactive rooms for the agent
            proactive_rooms = db.query(
                Tables.ROOMS.value,
                (Tables.ROOMS__agent_id.value, agent.id),
                (Tables.ROOMS__agent_proactivity.value, ">", 0),
            )

            for room in proactive_rooms:
                # Check if the room is eligible for revival
                if is_room_eligible_for_revival(db, room):
                    # Get the last message for the room
                    last_message = db.get_row(
                        Tables.MESSAGES.value,
                        {Tables.MESSAGES__room_id.value: room.id},
                        order_by=Tables.MESSAGES__created_at.value,
                        order_desc=True,
                    )

                    # Check if the room should be revived
                    if last_message and should_send_proactive_message(
                        agent_proactivity=room.agent_proactivity,
                        last_message_time=last_message.created_at,
                    ):
                        # Schedule the revive task
                        revive_task = ReviveTask(room_id=room.id)
                        scheduled_task_info = ScheduledTaskInfo(
                            task=revive_task, delay=0
                        )

                        TaskScheduler.schedule_task(
                            task_data=scheduled_task_info.to_dict(), delay=0, db=db
                        )

                        logger.info(f"Scheduled revive task for room {room.id}")

    except Exception as e:
        logger.error(f"Error in handle_revive: {str(e)}", exc_info=True)
        raise


def is_room_eligible_for_revival(db: SupabaseDB, room: RoomTableModel) -> bool:
    """
    Check if a room is eligible for revival based on subscription status.
    """
    if not room.subscribe_message_sent:
        return True

    # Check for an active subscription
    active_subscription = db.get_row(
        Tables.SUBSCRIPTIONS.value,
        {
            Tables.SUBSCRIPTIONS__room_id.value: room.id,
            Tables.SUBSCRIPTIONS__ended_at.value: None,
        },
    )

    return active_subscription is not None
