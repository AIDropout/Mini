from zootopia.database import SupabaseDB
from zootopia.core.schema import TaskType, ScheduleTableModel
from typing import Optional
from datetime import datetime
"""Function to schedule a message"""

"""
    SCHEDULE = "schedule"
    SCHEDULE__id = "id"
    SCHEDULE__room_id = "room_id"
    SCHEDULE__created_at = "created_at"
    SCHEDULE__run_at = "run_at"
    SCHEDULE__type = "type"  # respond, remind, revive
    SCHEDULE__info = "info"
    SCHEDULE__complete = "complete"
"""

# Calculate run_at
def schedule_to_table(db: SupabaseDB, task_type: TaskType, room_id: int, run_at: datetime, info: Optional[str]):
  model = ScheduleTableModel(
    room_id=room_id,
    run_at=run_at,
    type=task_type,
  )

  if info:
    model.info = info