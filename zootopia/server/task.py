"""Cancels the 1st message task if it's ongoing and a 2nd message comes in"""

import uuid
import aioredis
from aioredis import Redis
from zootopia.core.logger import logger

# Temp: To use
# cancel = CancelManager(config.CANCEL_CONFIG.REDIS_URL)
# await cancel.start_new_task(room_id)
# if await cancel.verify_latest_task():
#     print(f"😍Task cancelled: {room_id}")
#     return

# TODO: get redis url from config
class TaskManager:
    def __init__(self, room_id):
        self.client: Redis = aioredis.from_url("redis://127.0.0.1")   
        self.room_id: int = room_id 
        self.task_id: str = None

    async def start_new_task(self):
        self.task_id = str(uuid.uuid4())
        await self.client.set(
          f"room:{self.room_id}:task_id", self.task_id
        )
        return self.task_id

    async def verify_latest_task(self):
        latest_task_id = await self.client.get(
            f"room:{self.room_id}:task_id"
        )
        logger.info(f"This process' task id: {self.task_id}. 
                    Most recent process' task id: {latest_task_id.decode()}")
        return self.task_id == latest_task_id.decode()